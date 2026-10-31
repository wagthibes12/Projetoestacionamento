"""Fábrica de rotas CRUD para as tabelas simples do sistema.

Cada cadastro (clientes, veículos, vagas, preços) ganha as mesmas 5 rotas:
listar, obter, criar, atualizar e excluir. Escrever isso uma única vez evita
repetir (e errar de forma diferente) em cada cadastro.

Regras comuns a todos:
- Só operadores autenticados acessam.
- Quem criou, editou ou excluiu é sempre o operador do token, nunca um valor
  enviado pelo cliente da API.
- Excluir é lógico: o registro continua no banco, para preservar o histórico.
"""
import logging
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.models.base import agora_utc
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

# Executado dentro da mesma transação, antes de gravar um registro novo.
Gancho = Callable[[Session, Usuario, Any], None]

# Códigos de erro do MySQL/MariaDB mais comuns, traduzidos para o operador.
_ERROS_DO_BANCO: dict[int, tuple[int, str]] = {
    1062: (
        409,
        "Já existe um registro com este valor único (ex.: CPF/CNPJ, placa, código "
        "ou preço ativo). Se ele foi excluído antes, o valor continua reservado.",
    ),
    1452: (422, "Referência inválida: um dos registros relacionados não existe."),
    1451: (409, "Este registro está em uso por outros registros."),
    4025: (422, "Os dados violam uma regra de validação do banco."),
    3819: (422, "Os dados violam uma regra de validação do banco."),
}


def salvar(session: Session) -> None:
    """Confirma a transação, traduzindo erros de integridade em respostas claras."""
    try:
        session.commit()
    except IntegrityError as erro:
        session.rollback()
        logger.warning("Conflito ao salvar: %s", erro.orig)
        argumentos = getattr(erro.orig, "args", ())
        codigo = argumentos[0] if argumentos else None
        status, mensagem = _ERROS_DO_BANCO.get(
            codigo, (409, "Os dados conflitam com as regras do banco.")
        )
        raise HTTPException(status_code=status, detail=mensagem)


def buscar_ou_404(session: Session, modelo: type, item_id: int) -> Any:
    item = session.exec(
        select(modelo).where(
            col(modelo.id) == item_id,
            col(modelo.excluido_em).is_(None),
        )
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    return item


def criar_router_crud(
    *,
    modelo: type,
    entrada: type[BaseModel],
    atualizacao: type[BaseModel],
    saida: type[BaseModel],
    prefixo: str,
    tag: str,
    antes_de_criar: Gancho | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefixo, tags=[tag])
    SessaoDb = Annotated[Session, Depends(get_session)]

    @router.get("", response_model=list[saida])
    def listar(
        usuario: UsuarioAtual,
        session: SessaoDb,
        limite: int = Query(100, ge=1, le=500),
        deslocamento: int = Query(0, ge=0),
    ):
        consulta = (
            select(modelo)
            .where(col(modelo.excluido_em).is_(None))
            .order_by(col(modelo.id))
            .limit(limite)
            .offset(deslocamento)
        )
        return session.exec(consulta).all()

    @router.get("/{item_id}", response_model=saida)
    def obter(item_id: int, usuario: UsuarioAtual, session: SessaoDb):
        return buscar_ou_404(session, modelo, item_id)

    @router.post("", response_model=saida, status_code=201)
    def criar(dados: entrada, usuario: UsuarioAtual, session: SessaoDb):
        if antes_de_criar is not None:
            antes_de_criar(session, usuario, dados)
        item = modelo(**dados.model_dump(), criado_por=usuario.id)
        session.add(item)
        salvar(session)
        session.refresh(item)
        return item

    @router.patch("/{item_id}", response_model=saida)
    def atualizar(item_id: int, dados: atualizacao, usuario: UsuarioAtual, session: SessaoDb):
        item = buscar_ou_404(session, modelo, item_id)
        alteracoes = dados.model_dump(exclude_unset=True)
        if not alteracoes:
            raise HTTPException(status_code=422, detail="Nenhum campo foi informado.")
        colunas = modelo.__table__.columns
        for campo, valor in alteracoes.items():
            # Um campo obrigatório não pode ser apagado (enviado como null).
            if valor is None and not colunas[campo].nullable:
                raise HTTPException(
                    status_code=422, detail=f"O campo '{campo}' não pode ficar vazio."
                )
            setattr(item, campo, valor)
        item.atualizado_em = agora_utc()
        item.atualizado_por = usuario.id
        salvar(session)
        session.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=204)
    def excluir(item_id: int, usuario: UsuarioAtual, session: SessaoDb):
        item = buscar_ou_404(session, modelo, item_id)
        item.excluido_em = agora_utc()
        item.excluido_por = usuario.id
        salvar(session)

    return router