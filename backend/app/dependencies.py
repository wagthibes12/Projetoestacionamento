"""Dependências compartilhadas pelas rotas (identificação do operador logado)."""
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import ler_token_acesso
from app.models.usuario import Usuario
from app.repositories import usuario_repository

# auto_error=False: quem responde o erro 401 somos nós, com mensagem padronizada.
_esquema_bearer = HTTPBearer(auto_error=False)


def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Não autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_usuario_atual(
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)],
    session: Annotated[Session, Depends(get_session)],
) -> Usuario:
    if credenciais is None:
        raise _nao_autenticado()
    usuario_id = ler_token_acesso(credenciais.credentials)
    if usuario_id is None:
        raise _nao_autenticado()
    # O banco é consultado a cada requisição: um operador desativado ou
    # excluído perde o acesso na hora, mesmo com o token ainda dentro da validade.
    usuario = usuario_repository.buscar_por_id(session, usuario_id)
    if usuario is None or not usuario.ativo:
        raise _nao_autenticado()
    return usuario


# Uso nas rotas protegidas:  def minha_rota(usuario: UsuarioAtual): ...
UsuarioAtual = Annotated[Usuario, Depends(get_usuario_atual)]