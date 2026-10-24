
"""Rotas HTTP para o cadastro de clientes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.schemas.cliente import (
    ClienteCriar,
    ClienteAtualizar,
    ClienteResposta,
)
from app.services import cliente_service

router = APIRouter(prefix="/clientes", tags=["Clientes"])

SessaoDB = Annotated[Session, Depends(get_session)]


def tratar_erro_cliente(erro: Exception) -> None:
    if isinstance(erro, cliente_service.ClienteNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    if isinstance(erro, cliente_service.DocumentoDuplicado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cadastro com este CPF/CNPJ.",
        )

    if isinstance(erro, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        )


@router.get("/", response_model=list[ClienteResposta])
def listar_clientes(
    session: SessaoDB,
    usuario: UsuarioAtual,
    limite: Annotated[int, Query(ge=1, le=100)] = 100,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
):
    return cliente_service.listar_clientes(session, limite, deslocamento)


@router.get("/{cliente_id}", response_model=ClienteResposta)
def buscar_cliente(
    cliente_id: int,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        return cliente_service.buscar_cliente(session, cliente_id)
    except cliente_service.ClienteNaoEncontrado as erro:
        tratar_erro_cliente(erro)


@router.post(
    "/",
    response_model=ClienteResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_cliente(
    dados: ClienteCriar,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        return cliente_service.criar_cliente(session, dados, usuario.id)
    except (
        cliente_service.DocumentoDuplicado,
        IntegrityError,
    ) as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cadastro com este CPF/CNPJ.",
        ) from erro


@router.patch("/{cliente_id}", response_model=ClienteResposta)
def atualizar_cliente(
    cliente_id: int,
    dados: ClienteAtualizar,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        return cliente_service.atualizar_cliente(
            session, cliente_id, dados, usuario.id
        )
    except (
        cliente_service.ClienteNaoEncontrado,
        cliente_service.DocumentoDuplicado,
        ValueError,
        IntegrityError,
    ) as erro:
        session.rollback()
        tratar_erro_cliente(erro)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_cliente(
    cliente_id: int,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        cliente_service.excluir_cliente(
            session, cliente_id, usuario.id
        )
    except cliente_service.ClienteNaoEncontrado as erro:
        tratar_erro_cliente(erro)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
