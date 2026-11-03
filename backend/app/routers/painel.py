"""Rota do painel de vagas."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.dependencies import UsuarioAtual
from app.schemas.operacao import PainelSaida
from app.services import painel_service

router = APIRouter(prefix="/painel", tags=["Painel"])


@router.get("", response_model=PainelSaida)
def painel(usuario: UsuarioAtual, session: Annotated[Session, Depends(get_session)]):
    """Situação de cada vaga agora: livre, ocupada ou reservada a mensalista."""
    return painel_service.montar_painel(session)