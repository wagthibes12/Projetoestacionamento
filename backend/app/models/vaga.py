from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Vaga(SQLModel, table=True):
    __tablename__ = "vagas"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True, max_length=10)
    ativa: int = Field(default=1)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    criado_por: int = Field(foreign_key="usuarios.id")
    atualizado_em: Optional[datetime] = Field(default=None)
    atualizado_por: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    excluido_em: Optional[datetime] = Field(default=None)
    excluido_por: Optional[int] = Field(default=None, foreign_key="usuarios.id")