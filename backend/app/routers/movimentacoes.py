"""Rotas da operação diária: entrada, saída, cobrança e histórico de movimentações."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.models.enums import StatusMovimentacao
from app.schemas.operacao import CobrancaSaida, EntradaPedido, MovimentacaoDetalhe, SaidaPedido
from app.services import movimentacao_service

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])
SessaoDb = Annotated[Session, Depends(get_session)]


@router.post("/entrada", response_model=MovimentacaoDetalhe, status_code=201)
def registrar_entrada(dados: EntradaPedido, usuario: UsuarioAtual, session: SessaoDb):
    """Registra a entrada de um veículo. Sem vaga_id, escolhe uma vaga livre."""
    return movimentacao_service.registrar_entrada(session, usuario, dados)


@router.get("/abertas", response_model=list[MovimentacaoDetalhe])
def listar_abertas(usuario: UsuarioAtual, session: SessaoDb):
    """Veículos estacionados agora."""
    return movimentacao_service.listar_abertas(session)


@router.get("", response_model=list[MovimentacaoDetalhe])
def listar_historico(
    usuario: UsuarioAtual,
    session: SessaoDb,
    status: StatusMovimentacao | None = None,
    limite: int = Query(100, ge=1, le=500),
    deslocamento: int = Query(0, ge=0),
):
    """Histórico de movimentações, da mais recente para a mais antiga."""
    return movimentacao_service.listar_historico(session, status, limite, deslocamento)


@router.get("/{movimentacao_id}/cobranca", response_model=CobrancaSaida)
def simular_cobranca(movimentacao_id: int, usuario: UsuarioAtual, session: SessaoDb):
    """Mostra o valor a cobrar agora, sem registrar a saída."""
    return movimentacao_service.simular_cobranca(session, movimentacao_id)


@router.post("/{movimentacao_id}/saida", response_model=MovimentacaoDetalhe)
def registrar_saida(
    movimentacao_id: int,
    usuario: UsuarioAtual,
    session: SessaoDb,
    dados: SaidaPedido | None = None,
):
    """Registra a saída e grava o valor cobrado. Horista precisa informar a forma de pagamento."""
    forma_pagamento = dados.forma_pagamento if dados else None
    return movimentacao_service.registrar_saida(session, usuario, movimentacao_id, forma_pagamento)


@router.delete("/{movimentacao_id}", status_code=204)
def cancelar_movimentacao(movimentacao_id: int, usuario: UsuarioAtual, session: SessaoDb):
    """Cancela (exclusão lógica) uma movimentação lançada por engano."""
    movimentacao_service.cancelar_movimentacao(session, usuario, movimentacao_id)