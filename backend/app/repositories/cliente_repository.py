
"""Acesso ao banco para a tabela clientes_estacionamento.

Esta camada só fala com o banco: não valida regras de negócio nem conhece
requisições HTTP.
"""
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, col, select

from app.models.cliente import Cliente


def listar(session: Session, limite: int = 100, deslocamento: int = 0) -> list[Cliente]:
    consulta = (
        select(Cliente)
        .where(col(Cliente.excluido_em).is_(None))
        .order_by(Cliente.nome)
        .offset(deslocamento)
        .limit(limite)
    )
    return list(session.exec(consulta).all())


def buscar_por_id(session: Session, cliente_id: int) -> Cliente | None:
    consulta = select(Cliente).where(
        col(Cliente.id) == cliente_id,
        col(Cliente.excluido_em).is_(None),
    )
    return session.exec(consulta).first()



def buscar_por_cpf_cnpj(
    session: Session,
    cpf_cnpj: str,
) -> Cliente | None:
    """Busca o documento apenas entre clientes não excluídos."""

    consulta = select(Cliente).where(
        Cliente.cpf_cnpj == cpf_cnpj,
        col(Cliente.excluido_em).is_(None),
    )

    return session.exec(consulta).first()



def criar(session: Session, cliente: Cliente) -> Cliente:
    try:
        session.add(cliente)
        session.commit()
        session.refresh(cliente)
        return cliente
    except SQLAlchemyError:
        session.rollback()
        raise


def salvar(session: Session, cliente: Cliente) -> Cliente:
    try:
        session.add(cliente)
        session.commit()
        session.refresh(cliente)
        return cliente
    except SQLAlchemyError:
        session.rollback()
        raise
