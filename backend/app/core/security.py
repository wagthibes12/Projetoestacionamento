"""Hash de senha e token de acesso (JWT)."""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

# Argon2id é o algoritmo recomendado hoje para senhas. Cada hash já embute um
# "sal" aleatório, então duas senhas iguais geram hashes diferentes.
_hasher = PasswordHasher()


def gerar_hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        # Senha errada ou hash inválido: nos dois casos o acesso é negado, sem
        # detalhar o motivo.
        return False


def criar_token_acesso(usuario_id: int) -> str:
    settings = get_settings()
    agora = datetime.now(timezone.utc)
    # O token carrega só o id do operador: nada de senha ou dados pessoais,
    # porque o conteúdo de um JWT pode ser lido por quem o possui.
    payload = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(
        payload, settings.secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def ler_token_acesso(token: str) -> int | None:
    """Devolve o id do operador se o token for válido, ou None caso contrário."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            # Lista explícita de algoritmos aceitos: impede que um token
            # forjado escolha o algoritmo (ex.: "none") para escapar da assinatura.
            algorithms=[settings.jwt_algorithm],
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        # Assinatura inválida, token expirado, formato errado, etc.
        return None