"""Partes reutilizadas pelos formatos de saída da API."""
from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


def _como_utc(valor: datetime) -> datetime:
    # O banco guarda as datas em UTC, sem fuso. Ao enviar para fora, o fuso é
    # anexado: sem ele, o navegador leria "2026-10-23T22:00:00" como horário
    # LOCAL e mostraria a hora errada.
    return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor


DataHoraUTC = Annotated[datetime, AfterValidator(_como_utc)]


class SaidaBase(BaseModel):
    """Campos comuns de toda resposta que representa um registro do banco."""

    # Permite montar a resposta direto a partir do modelo do banco.
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: DataHoraUTC
    criado_por: int | None = None
    atualizado_em: DataHoraUTC | None = None
    atualizado_por: int | None = None