"""Rotas do cadastro de operadores (quem acessa o sistema)."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.schemas.operadores import OperadorAtualizacao, OperadorEntrada, OperadorSaida
from app.services import operador_service

router = APIRouter(prefix="/operadores", tags=["Operadores"])
SessaoDb = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[OperadorSaida])
def listar(usuario: UsuarioAtual, session: SessaoDb):
    return [OperadorSaida.model_validate(o) for o in operador_service.listar(session)]


@router.post("", response_model=OperadorSaida, status_code=201)
def criar(dados: OperadorEntrada, usuario: UsuarioAtual, session: SessaoDb):
    return OperadorSaida.model_validate(operador_service.criar(session, usuario, dados))


@router.patch("/{operador_id}", response_model=OperadorSaida)
def atualizar(operador_id: int, dados: OperadorAtualizacao, usuario: UsuarioAtual, session: SessaoDb):
    return OperadorSaida.model_validate(
        operador_service.atualizar(session, usuario, operador_id, dados)
    )


@router.delete("/{operador_id}", status_code=204)
def excluir(operador_id: int, usuario: UsuarioAtual, session: SessaoDb):
    operador_service.excluir(session, usuario, operador_id)