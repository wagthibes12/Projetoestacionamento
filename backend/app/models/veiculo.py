from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class VeiculoEstacionamento(SQLModel, table=True):
    __tablename__ = "veiculos_estacionamento"

    id: Optional[int] = Field(default=None, primary_key=True)
    placa: str = Field(index=True, unique=True, max_length=7)
    tipo: str = Field(default="CARRO")  # 'CARRO', 'MOTO', 'OUTRO'
    modelo: Optional[str] = Field(default=None, max_length=60)
    cor: Optional[str] = Field(default=None, max_length=30)
    cliente_id: Optional[int] = Field(default=None, foreign_key="clientes.id")
    ativo: int = Field(default=1)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    criado_por: int = Field(foreign_key="usuarios.id")
    atualizado_em: Optional[datetime] = Field(default=None)
    atualizado_por: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    excluido_em: Optional[datetime] = Field(default=None)
    excluido_por: Optional[int] = Field(default=None, foreign_key="usuarios.id")