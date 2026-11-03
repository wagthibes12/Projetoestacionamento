"""Formato dos dados da operação do estacionamento: entrada, saída, cobrança e painel."""
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator

from app.core.validadores import normalizar_placa
from app.models.enums import FormaPagamento, StatusMovimentacao, TipoCobranca, TipoVeiculo
from app.schemas.comum import DataHoraUTC


class EntradaPedido(BaseModel):
    placa: str
    # Usado só quando o veículo ainda não está cadastrado (horista avulso).
    tipo_veiculo: TipoVeiculo = TipoVeiculo.CARRO
    # Opcional: se omitido, o sistema escolhe uma vaga livre.
    vaga_id: int | None = None

    @field_validator("placa")
    @classmethod
    def _validar_placa(cls, valor: str) -> str:
        return normalizar_placa(valor)


class SaidaPedido(BaseModel):
    # Obrigatória para horista. Para mensalista é ignorada, porque a cobrança
    # dele vai pela mensalidade.
    forma_pagamento: FormaPagamento | None = None


class MovimentacaoDetalhe(BaseModel):
    id: int
    tipo: TipoCobranca
    veiculo_id: int
    placa: str
    vaga_id: int
    vaga_codigo: str
    entrada_em: DataHoraUTC
    saida_em: DataHoraUTC | None = None
    valor_cobrado: Decimal | None = None
    forma_pagamento: FormaPagamento | None = None
    status: StatusMovimentacao


class CobrancaSaida(BaseModel):
    movimentacao_id: int
    tipo: TipoCobranca
    placa: str
    entrada_em: DataHoraUTC
    # Momento usado no cálculo (agora, enquanto a saída não foi registrada).
    calculado_em: DataHoraUTC
    minutos: int
    horas_cobradas: int
    valor_hora: Decimal | None = None
    valor_total: Decimal


class VagaPainel(BaseModel):
    vaga_id: int
    codigo: str
    situacao: Literal["LIVRE", "OCUPADA", "RESERVADA"]
    placa: str | None = None
    tipo: TipoCobranca | None = None
    movimentacao_id: int | None = None
    entrada_em: DataHoraUTC | None = None


class PainelSaida(BaseModel):
    total: int
    livres: int
    ocupadas: int
    reservadas: int
    vagas: list[VagaPainel]