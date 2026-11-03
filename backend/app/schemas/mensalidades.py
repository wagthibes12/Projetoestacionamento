"""Formato dos dados das mensalidades."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import FormaPagamento, StatusMensalidade
from app.schemas.comum import DataHoraUTC

# Mês de referência no formato AAAA-MM, por exemplo 2026-11.
PADRAO_COMPETENCIA = r"^\d{4}-(0[1-9]|1[0-2])$"


class GerarPedido(BaseModel):
    competencia: str = Field(pattern=PADRAO_COMPETENCIA)


class GerarSaida(BaseModel):
    competencia: date
    criadas: int
    ja_existiam: int


class PagamentoPedido(BaseModel):
    forma_pagamento: FormaPagamento


class MensalidadeDetalhe(BaseModel):
    id: int
    mensalista_id: int
    cliente_nome: str
    placa: str
    vaga_codigo: str
    competencia: date
    valor: Decimal
    vencimento: date
    status: StatusMensalidade
    pago_em: DataHoraUTC | None = None
    forma_pagamento: FormaPagamento | None = None