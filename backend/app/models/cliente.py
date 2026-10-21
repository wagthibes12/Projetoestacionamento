"""Modelo da tabela clientes_estacionamento (apenas cadastro; cliente não acessa o sistema)."""
from sqlmodel import Field

from app.models.base import AuditoriaBase


class Cliente(AuditoriaBase, table=True):
    __tablename__ = "clientes_estacionamento"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=150)
    # Somente dígitos: 11 (CPF) ou 14 (CNPJ). O banco confere só o tamanho; o
    # cálculo dos dígitos verificadores fica na validação do backend.
    cpf_cnpj: str = Field(max_length=14, unique=True)
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=150)
    ativo: bool = Field(default=True)