"""Regras de negócio do cadastro de operadores."""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.core.security import gerar_hash_senha
from app.models import Usuario
from app.models.base import agora_utc
from app.repositories import usuario_repository
from app.schemas.operadores import OperadorAtualizacao, OperadorEntrada


def listar(session: Session) -> list[Usuario]:
    return list(
        session.exec(
            select(Usuario).where(col(Usuario.excluido_em).is_(None)).order_by(col(Usuario.id))
        ).all()
    )


def criar(session: Session, logado: Usuario, dados: OperadorEntrada) -> Usuario:
    operador = Usuario(
        nome=dados.nome,
        login=dados.login,
        senha_hash=gerar_hash_senha(dados.senha),
        criado_por=logado.id,
    )
    session.add(operador)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Já existe um operador com este login (mesmo excluído, o login continua reservado).",
        )
    session.refresh(operador)
    return operador


def _buscar(session: Session, operador_id: int) -> Usuario:
    operador = usuario_repository.buscar_por_id(session, operador_id)
    if operador is None:
        raise HTTPException(status_code=404, detail="Operador não encontrado.")
    return operador


def atualizar(session: Session, logado: Usuario, operador_id: int, dados: OperadorAtualizacao) -> Usuario:
    operador = _buscar(session, operador_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    if not alteracoes:
        raise HTTPException(status_code=422, detail="Nenhum campo foi informado.")
    for campo in ("nome", "senha", "ativo"):
        if campo in alteracoes and alteracoes[campo] is None:
            raise HTTPException(status_code=422, detail=f"O campo '{campo}' não pode ficar vazio.")
    # Evita que o operador se tranque para fora do sistema sem querer.
    if alteracoes.get("ativo") is False and operador.id == logado.id:
        raise HTTPException(status_code=409, detail="Você não pode desativar o seu próprio acesso.")

    if "nome" in alteracoes:
        operador.nome = alteracoes["nome"]
    if "senha" in alteracoes:
        operador.senha_hash = gerar_hash_senha(alteracoes["senha"])
    if "ativo" in alteracoes:
        operador.ativo = alteracoes["ativo"]
    operador.atualizado_em = agora_utc()
    operador.atualizado_por = logado.id
    session.commit()
    session.refresh(operador)
    return operador


def excluir(session: Session, logado: Usuario, operador_id: int) -> None:
    operador = _buscar(session, operador_id)
    if operador.id == logado.id:
        raise HTTPException(status_code=409, detail="Você não pode excluir o seu próprio acesso.")
    operador.excluido_em = agora_utc()
    operador.excluido_por = logado.id
    session.commit()