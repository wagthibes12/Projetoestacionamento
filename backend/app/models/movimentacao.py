"""Modelo da tabela movimentacoes (entrada e saída de veículos)."""
from datetime import datetime
from decimal import Decimal

from sqlmodel import Field

from app.models.base import USUARIOS_ID, AuditoriaBase, agora_utc
from app.models.enums import FormaPagamento, StatusMovimentacao, TipoCobranca


class Movimentacao(AuditoriaBase, table=True):
    __tablename__ = "movimentacoes"

    id: int | None = Field(default=None, primary_key=True)
    tipo: TipoCobranca
    veiculo_id: int = Field(foreign_key="veiculos_estacionamento.id")
    vaga_id: int = Field(foreign_key="vagas.id")
    # Entrada e saída usam o mesmo relógio (o da API, em UTC): é a base do
    # valor cobrado.
    entrada_em: datetime = Field(default_factory=agora_utc)
    saida_em: datetime | None = None
    # Gravado na saída, o que preserva o preço da época. Mensalista fica 0.00,
    # pois a cobrança vai pela mensalidade.
    valor_cobrado: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    forma_pagamento: FormaPagamento | None = None
    status: StatusMovimentacao = Field(default=StatusMovimentacao.ABERTA)
    # Operador que registrou a saída (quem registrou a entrada é o criado_por).
    finalizado_por: int | None = Field(default=None, foreign_key=USUARIOS_ID)
    # "veiculo_aberto" e "vaga_aberta" existem no banco, mas ficam fora do
    # modelo de propósito: são colunas GERADAS (impedem duas movimentações
    # abertas para o mesmo veículo ou a mesma vaga). Incluí-las faria o INSERT
    # falhar.