"""Modelo da tabela vagas."""
from sqlmodel import Field

from app.models.base import AuditoriaBase


class Vaga(AuditoriaBase, table=True):
    __tablename__ = "vagas"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(max_length=10, unique=True)  # ex.: A01
    ativa: bool = Field(default=True)
    # Não existe campo "ocupada" de propósito: a ocupação é derivada das
    # movimentações abertas. Um campo duplicado ficaria dessincronizado.