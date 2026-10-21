"""Modelo da tabela veiculos_estacionamento."""
from sqlmodel import Field

from app.models.base import AuditoriaBase
from app.models.enums import TipoVeiculo


class Veiculo(AuditoriaBase, table=True):
    __tablename__ = "veiculos_estacionamento"

    id: int | None = Field(default=None, primary_key=True)
    # Normalizada antes de gravar: maiúscula e sem hífen (7 caracteres), para
    # a mesma placa não ser cadastrada duas vezes com formatos diferentes.
    placa: str = Field(max_length=7, unique=True)
    tipo: TipoVeiculo = Field(default=TipoVeiculo.CARRO)
    modelo: str | None = Field(default=None, max_length=60)
    cor: str | None = Field(default=None, max_length=30)
    # Opcional: o horista avulso não tem cadastro de cliente, basta a placa.
    cliente_id: int | None = Field(default=None, foreign_key="clientes_estacionamento.id")
    ativo: bool = Field(default=True)