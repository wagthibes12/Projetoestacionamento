
"""Rotas HTTP para o cadastro de veículos."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.schemas.veiculo import (
    VeiculoCriar,
    VeiculoAtualizar,
    VeiculoResposta,
)
from app.services import veiculo_service

router = APIRouter(prefix="/veiculos", tags=["Veículos"])

SessaoDB = Annotated[Session, Depends(get_session)]


def tratar_erro_veiculo(erro: Exception) -> None:
    if isinstance(erro, veiculo_service.VeiculoNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado.",
        )

    if isinstance(erro, veiculo_service.PlacaDuplicada):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um veículo ativo com esta placa.",
        )

    if isinstance(erro, veiculo_service.ClienteVeiculoInvalido):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O cliente informado não existe ou está inativo.",
        )

    if isinstance(erro, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        )


@router.get("/", response_model=list[VeiculoResposta])
def listar_veiculos(
    session: SessaoDB,
    usuario: UsuarioAtual,
    limite: Annotated[int, Query(ge=1, le=100)] = 100,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
):
    return veiculo_service.listar_veiculos(session, limite, deslocamento)


@router.get("/{veiculo_id}", response_model=VeiculoResposta)
def buscar_veiculo(
    veiculo_id: int,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        return veiculo_service.buscar_veiculo(session, veiculo_id)
    except veiculo_service.VeiculoNaoEncontrado as erro:
        tratar_erro_veiculo(erro)


@router.post(
    "/",
    response_model=VeiculoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_veiculo(
    dados: VeiculoCriar,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        return veiculo_service.criar_veiculo(
            session,
            dados,
            usuario.id,
        )
    except (
        veiculo_service.PlacaDuplicada,
        veiculo_service.ClienteVeiculoInvalido,
        IntegrityError,
    ) as erro:
        session.rollback()

        if isinstance(erro, IntegrityError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não foi possível cadastrar o veículo. "
                "Verifique se a placa já está em uso.",
            ) from erro

        tratar_erro_veiculo(erro)


@router.patch("/{veiculo_id}", response_model=VeiculoResposta)
def atualizar_veiculo(
    veiculo_id: int,
    dados: VeiculoAtualizar,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        return veiculo_service.atualizar_veiculo(
            session,
            veiculo_id,
            dados,
            usuario.id,
        )
    except (
        veiculo_service.VeiculoNaoEncontrado,
        veiculo_service.PlacaDuplicada,
        veiculo_service.ClienteVeiculoInvalido,
        ValueError,
        IntegrityError,
    ) as erro:
        session.rollback()

        if isinstance(erro, IntegrityError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não foi possível atualizar o veículo. "
                "Verifique a placa e o cliente informado.",
            ) from erro

        tratar_erro_veiculo(erro)


@router.delete(
    "/{veiculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_veiculo(
    veiculo_id: int,
    session: SessaoDB,
    usuario: UsuarioAtual,
):
    try:
        veiculo_service.excluir_veiculo(
            session,
            veiculo_id,
            usuario.id,
        )
    except veiculo_service.VeiculoNaoEncontrado as erro:
        tratar_erro_veiculo(erro)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
