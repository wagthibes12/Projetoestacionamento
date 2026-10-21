"""Modelo da tabela mensalistas (contrato: cliente + veículo + vaga fixa)."""
from decimal import Decimal

from sqlmodel import Field

from app.models.base import AuditoriaBase


class Mensalista(AuditoriaBase, table=True):
    __tablename__ = "mensalistas"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="clientes_estacionamento.id")
    veiculo_id: int = Field(foreign_key="veiculos_estacionamento.id")
    vaga_id: int = Field(foreign_key="vagas.id")
    # Copiado de "precos" na assinatura, para uma mudança futura de preço não
    # alterar contratos já firmados.
    valor_mensal: Decimal = Field(max_digits=10, decimal_places=2)
    # Até 28, para o vencimento existir em todos os meses (inclusive fevereiro).
    dia_vencimento: int = Field(ge=1, le=28)
    ativo: bool = Field(default=True)
    # "vaga_ativa" e "veiculo_ativo" existem no banco, mas ficam fora do modelo
    # de propósito: são colunas GERADAS (garantem um único contrato vigente por
    # vaga e por veículo). Incluí-las faria o INSERT falhar.