"""Modelo da tabela precos."""
from decimal import Decimal

from sqlmodel import Field

from app.models.base import AuditoriaBase
from app.models.enums import TipoCobranca


class Preco(AuditoriaBase, table=True):
    __tablename__ = "precos"

    id: int | None = Field(default=None, primary_key=True)
    tipo: TipoCobranca
    # HORISTA: valor por hora. MENSALISTA: valor mensal. Decimal, nunca float,
    # para não acumular erro de arredondamento nas cobranças.
    valor: Decimal = Field(max_digits=10, decimal_places=2)
    ativo: bool = Field(default=True)
    # A coluna "tipo_ativo" existe no banco, mas fica fora do modelo de
    # propósito: ela é GERADA pelo banco (garante um único preço vigente por
    # tipo). Incluí-la faria o INSERT falhar.