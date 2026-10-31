"""Formato dos dados de entrada e saída dos cadastros básicos.

Ficam separados dos modelos de tabela para a API nunca aceitar nem expor
campos internos (como criado_por, que é sempre preenchido pelo backend).
"""
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.core.validadores import normalizar_cpf_cnpj, normalizar_placa
from app.models.enums import TipoCobranca, TipoVeiculo
from app.schemas.comum import SaidaBase

# strip_whitespace remove espaços antes de conferir o tamanho mínimo.
Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
CodigoVaga = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=10)
]
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# ---------------------------------------------------------------- clientes
class ClienteEntrada(BaseModel):
    nome: Nome
    cpf_cnpj: str
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=150, pattern=EMAIL)
    ativo: bool = True

    @field_validator("cpf_cnpj")
    @classmethod
    def _validar_documento(cls, valor: str) -> str:
        return normalizar_cpf_cnpj(valor)


class ClienteAtualizacao(BaseModel):
    nome: Nome | None = None
    cpf_cnpj: str | None = None
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=150, pattern=EMAIL)
    ativo: bool | None = None

    @field_validator("cpf_cnpj")
    @classmethod
    def _validar_documento(cls, valor: str | None) -> str | None:
        return None if valor is None else normalizar_cpf_cnpj(valor)


class ClienteSaida(SaidaBase):
    nome: str
    cpf_cnpj: str
    telefone: str | None = None
    email: str | None = None
    ativo: bool


# ---------------------------------------------------------------- veículos
class VeiculoEntrada(BaseModel):
    placa: str
    tipo: TipoVeiculo = TipoVeiculo.CARRO
    modelo: str | None = Field(default=None, max_length=60)
    cor: str | None = Field(default=None, max_length=30)
    cliente_id: int | None = None
    ativo: bool = True

    @field_validator("placa")
    @classmethod
    def _validar_placa(cls, valor: str) -> str:
        return normalizar_placa(valor)


class VeiculoAtualizacao(BaseModel):
    placa: str | None = None
    tipo: TipoVeiculo | None = None
    modelo: str | None = Field(default=None, max_length=60)
    cor: str | None = Field(default=None, max_length=30)
    cliente_id: int | None = None
    ativo: bool | None = None

    @field_validator("placa")
    @classmethod
    def _validar_placa(cls, valor: str | None) -> str | None:
        return None if valor is None else normalizar_placa(valor)


class VeiculoSaida(SaidaBase):
    placa: str
    tipo: TipoVeiculo
    modelo: str | None = None
    cor: str | None = None
    cliente_id: int | None = None
    ativo: bool


# ------------------------------------------------------------------- vagas
class VagaEntrada(BaseModel):
    codigo: CodigoVaga
    ativa: bool = True


class VagaAtualizacao(BaseModel):
    codigo: CodigoVaga | None = None
    ativa: bool | None = None


class VagaSaida(SaidaBase):
    codigo: str
    ativa: bool


# ------------------------------------------------------------------ preços
class PrecoEntrada(BaseModel):
    tipo: TipoCobranca
    # HORISTA: valor por hora. MENSALISTA: valor mensal.
    valor: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    ativo: bool = True


class PrecoAtualizacao(BaseModel):
    tipo: TipoCobranca | None = None
    valor: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    ativo: bool | None = None


class PrecoSaida(SaidaBase):
    tipo: TipoCobranca
    valor: Decimal
    ativo: bool