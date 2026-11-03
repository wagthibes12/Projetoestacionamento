"""Rotas das mensalidades: gerar, listar, pagar, cancelar e excluir."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.models.enums import StatusMensalidade
from app.schemas.mensalidades import (
    PADRAO_COMPETENCIA,
    GerarPedido,
    GerarSaida,
    MensalidadeDetalhe,
    PagamentoPedido,
)
from app.services import mensalidade_service

router = APIRouter(prefix="/mensalidades", tags=["Mensalidades"])
SessaoDb = Annotated[Session, Depends(get_session)]


@router.post("/gerar", response_model=GerarSaida)
def gerar(dados: GerarPedido, usuario: UsuarioAtual, session: SessaoDb):
    """Gera a mensalidade do mês (AAAA-MM) para cada contrato ativo. Pode ser repetida."""
    return mensalidade_service.gerar(session, usuario, dados.competencia)


@router.get("", response_model=list[MensalidadeDetalhe])
def listar(
    usuario: UsuarioAtual,
    session: SessaoDb,
    competencia: str | None = Query(default=None, pattern=PADRAO_COMPETENCIA),
    status: StatusMensalidade | None = None,
):
    return mensalidade_service.listar(session, competencia, status)


@router.post("/{mensalidade_id}/pagar", response_model=MensalidadeDetalhe)
def pagar(mensalidade_id: int, dados: PagamentoPedido, usuario: UsuarioAtual, session: SessaoDb):
    return mensalidade_service.pagar(session, usuario, mensalidade_id, dados.forma_pagamento)


@router.post("/{mensalidade_id}/cancelar", response_model=MensalidadeDetalhe)
def cancelar(mensalidade_id: int, usuario: UsuarioAtual, session: SessaoDb):
    return mensalidade_service.cancelar(session, usuario, mensalidade_id)


@router.delete("/{mensalidade_id}", status_code=204)
def excluir(mensalidade_id: int, usuario: UsuarioAtual, session: SessaoDb):
    mensalidade_service.excluir(session, usuario, mensalidade_id)