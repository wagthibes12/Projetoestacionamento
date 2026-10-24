
"""Schemas de entrada e saída para veículos."""

import re

from pydantic import ConfigDict, field_validator
from sqlmodel import SQLModel

from app.models.enums import TipoVeiculo


def normalizar_placa(valor: str) -> str:
    """Normaliza e valida placas brasileiras antigas e padrão Mercosul."""

    placa = re.sub(r"[^A-Za-z0-9]", "", valor).upper()

    if len(placa) != 7:
        raise ValueError("A placa deve conter 7 caracteres.")

    # Aceita placas antigas e padrão Mercosul.
    if not re.fullmatch(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}", placa):
        raise ValueError("Informe uma placa válida.")

    return placa


class VeiculoCriar(SQLModel):
    placa: str
    tipo: TipoVeiculo = TipoVeiculo.CARRO
    modelo: str | None = None
    cor: str | None = None
    cliente_id: int | None = None

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str) -> str:
        return normalizar_placa(valor)

    @field_validator("modelo")
    @classmethod
    def validar_modelo(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()
            if len(valor) > 60:
                raise ValueError("O modelo deve ter no máximo 60 caracteres.")
            return valor or None
        return valor

    @field_validator("cor")
    @classmethod
    def validar_cor(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()
            if len(valor) > 30:
                raise ValueError("A cor deve ter no máximo 30 caracteres.")
            return valor or None
        return valor

    @field_validator("cliente_id")
    @classmethod
    def validar_cliente_id(cls, valor: int | None) -> int | None:
        if valor is not None and valor <= 0:
            raise ValueError("O cliente informado é inválido.")
        return valor


class VeiculoAtualizar(SQLModel):
    placa: str | None = None
    tipo: TipoVeiculo | None = None
    modelo: str | None = None
    cor: str | None = None
    cliente_id: int | None = None
    ativo: bool | None = None

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str | None) -> str | None:
        if valor is not None:
            return normalizar_placa(valor)
        return valor

    @field_validator("modelo")
    @classmethod
    def validar_modelo(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()
            if len(valor) > 60:
                raise ValueError("O modelo deve ter no máximo 60 caracteres.")
            return valor or None
        return valor

    @field_validator("cor")
    @classmethod
    def validar_cor(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()
            if len(valor) > 30:
                raise ValueError("A cor deve ter no máximo 30 caracteres.")
            return valor or None
        return valor

    @field_validator("cliente_id")
    @classmethod
    def validar_cliente_id(cls, valor: int | None) -> int | None:
        if valor is not None and valor <= 0:
            raise ValueError("O cliente informado é inválido.")
        return valor


class VeiculoResposta(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    placa: str
    tipo: TipoVeiculo
    modelo: str | None
    cor: str | None
    cliente_id: int | None
    ativo: bool
