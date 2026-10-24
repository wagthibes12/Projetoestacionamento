"""Acesso ao banco para a tabela usuarios_estacionamento.

Esta camada só fala com o banco: não valida regras de negócio nem conhece
requisições HTTP.
"""
from sqlmodel import Session, col, select

from app.models.usuario import Usuario


def existe_algum(session: Session) -> bool:
    return session.exec(select(Usuario.id).limit(1)).first() is not None


def buscar_por_id(session: Session, usuario_id: int) -> Usuario | None:
    # Operadores excluídos (exclusão lógica) deixam de existir para o sistema.
    consulta = select(Usuario).where(
        col(Usuario.id) == usuario_id,
        col(Usuario.excluido_em).is_(None),
    )
    return session.exec(consulta).first()


def buscar_por_login(session: Session, login: str) -> Usuario | None:
    # Operadores excluídos (exclusão lógica) não podem mais entrar no sistema.
    consulta = select(Usuario).where(
        Usuario.login == login,
        col(Usuario.excluido_em).is_(None),
    )
    return session.exec(consulta).first()


def criar(session: Session, usuario: Usuario) -> Usuario:
    session.add(usuario)
    session.commit()
    # Recarrega do banco para trazer o id gerado e os valores finais.
    session.refresh(usuario)
    return usuario