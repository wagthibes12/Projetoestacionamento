"""Rotas de autenticação: login e consulta do operador logado."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import criar_token_acesso
from app.dependencies import UsuarioAtual
from app.schemas.auth import LoginEntrada, TokenSaida, UsuarioSaida
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenSaida)
def login(dados: LoginEntrada, session: Session = Depends(get_session)) -> TokenSaida:
    usuario = auth_service.autenticar(session, dados.login, dados.senha)
    if usuario is None:
        # Mesma mensagem para login inexistente, senha errada e operador
        # desativado: não revela qual dos três aconteceu.
        raise HTTPException(
            status_code=401,
            detail="Login ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenSaida(access_token=criar_token_acesso(usuario.id))


@router.get("/eu", response_model=UsuarioSaida)
def operador_logado(usuario: UsuarioAtual):
    """Devolve o operador dono do token. Serve para testar a autenticação."""
    return usuario