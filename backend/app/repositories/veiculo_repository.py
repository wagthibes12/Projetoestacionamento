
"""Acesso ao banco para a tabela veiculos_estacionamento.

Esta camada só fala com o banco: não valida regras de negócio nem conhece
requisições HTTP.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, col, select

from app.models.veiculo import Veiculo


def listar(
    session: Session,
    limite: int = 100,
    deslocamento: int = 0,
) -> list[Veiculo]:
    """Lista veículos que não foram excluídos logicamente."""

    consulta = (
        select(Veiculo)
        .where(col(Veiculo.excluido_em).is_(None))
        .order_by(Veiculo.placa)
        .offset(deslocamento)
        .limit(limite)
    )

    return list(session.exec(consulta).all())


def buscar_por_id(
    session: Session,
    veiculo_id: int,
) -> Veiculo | None:
    """Busca um veículo pelo ID, ignorando os excluídos."""

    consulta = select(Veiculo).where(
        col(Veiculo.id) == veiculo_id,
        col(Veiculo.excluido_em).is_(None),
    )

    return session.exec(consulta).first()


def buscar_por_placa(
    session: Session,
    placa: str,
) -> Veiculo | None:
    """Busca a placa apenas entre veículos não excluídos."""

    consulta = select(Veiculo).where(
        Veiculo.placa == placa,
        col(Veiculo.excluido_em).is_(None),
    )

    return session.exec(consulta).first()


def criar(session: Session, veiculo: Veiculo) -> Veiculo:
    """Insere um veículo e devolve o registro persistido."""

    try:
        session.add(veiculo)
        session.commit()
        session.refresh(veiculo)
        return veiculo

    except SQLAlchemyError:
        session.rollback()
        raise


def salvar(session: Session, veiculo: Veiculo) -> Veiculo:
    """Salva alterações de um veículo existente."""

    try:
        session.add(veiculo)
        session.commit()
        session.refresh(veiculo)
        return veiculo

    except SQLAlchemyError:
        session.rollback()
        raise
