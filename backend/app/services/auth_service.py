"""Regras de negócio do login."""
from sqlmodel import Session

from app.core.security import gerar_hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.repositories import usuario_repository

# Quando o login não existe, ainda assim calculamos um hash. Sem isso, "login
# inexistente" responderia mais rápido que "senha errada", e quem tentasse
# acessar o sistema poderia descobrir quais logins existem pela diferença de
# tempo.
_HASH_FALSO = gerar_hash_senha("hash-falso-para-igualar-o-tempo")


def autenticar(session: Session, login: str, senha: str) -> Usuario | None:
    """Devolve o operador se login e senha estiverem corretos, ou None."""
    usuario = usuario_repository.buscar_por_login(session, login.strip().lower())
    if usuario is None:
        verificar_senha(senha, _HASH_FALSO)
        return None
    # A senha é conferida antes do "ativo" para o tempo de resposta não revelar
    # que o login existe, mas está desativado.
    if not verificar_senha(senha, usuario.senha_hash) or not usuario.ativo:
        return None
    return usuario