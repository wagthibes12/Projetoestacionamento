"""Modelo da tabela mensalidades (cobrança mensal dos mensalistas)."""
from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Field

from app.models.base import USUARIOS_ID, AuditoriaBase
from app.models.enums import FormaPagamento, StatusMensalidade


class Mensalidade(AuditoriaBase, table=True):
    __tablename__ = "mensalidades"

    id: int | None = Field(default=None, primary_key=True)
    mensalista_id: int = Field(foreign_key="mensalistas.id")
    # Sempre o 1º dia do mês de referência. Há uma mensalidade por contrato e
    # por mês (garantido por índice único no banco).
    competencia: date
    valor: Decimal = Field(max_digits=10, decimal_places=2)
    # Data informativa da cobrança. O sistema não verifica atraso.
    vencimento: date
    status: StatusMensalidade = Field(default=StatusMensalidade.PENDENTE)
    # Os três campos abaixo só são preenchidos quando a mensalidade é paga.
    pago_em: datetime | None = None
    forma_pagamento: FormaPagamento | None = None
    recebido_por: int | None = Field(default=None, foreign_key=USUARIOS_ID)