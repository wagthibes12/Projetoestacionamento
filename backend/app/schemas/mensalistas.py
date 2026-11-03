"""Formato dos dados dos contratos de mensalistas."""
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.comum import SaidaBase


class MensalistaEntrada(BaseModel):
    cliente_id: int
    veiculo_id: int
    vaga_id: int
    # Se omitido, usa o preço de mensalista vigente.
    valor_mensal: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    # Até 28, para o vencimento existir em todos os meses (inclusive fevereiro).
    dia_vencimento: int = Field(ge=1, le=28)
    ativo: bool = True


class MensalistaAtualizacao(BaseModel):
    # Cliente, veículo e vaga não mudam depois de criados. Para trocar, encerre
    # o contrato (ativo = false) e crie outro.
    valor_mensal: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    dia_vencimento: int | None = Field(default=None, ge=1, le=28)
    ativo: bool | None = None


class MensalistaSaida(SaidaBase):
    cliente_id: int
    veiculo_id: int
    vaga_id: int
    valor_mensal: Decimal
    dia_vencimento: int
    ativo: bool