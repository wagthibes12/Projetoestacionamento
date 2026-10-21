"""Campos comuns a todas as tabelas do sistema (auditoria)."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

# Todas as colunas "*_por" apontam para a tabela de operadores.
USUARIOS_ID = "usuarios_estacionamento.id"


def agora_utc() -> datetime:
    # O banco guarda as datas em UTC, em colunas DATETIME (sem fuso). Gerar o
    # valor aqui, já em UTC e sem tzinfo, evita misturar datetime "com fuso" e
    # "sem fuso" ao gravar e ler. A conversão para o horário local é feita só
    # na exibição.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditoriaBase(SQLModel):
    """Bloco de auditoria igual nas 8 tabelas: quem e quando criou, editou e excluiu.

    Não é uma tabela (sem table=True): serve apenas de base para os modelos,
    para não repetir esses seis campos em cada um.

    Quem preenche os campos "*_por" é sempre o backend, a partir do usuário
    autenticado, nunca o frontend, para ninguém forjar a autoria.
    """

    criado_em: datetime = Field(default_factory=agora_utc)
    criado_por: int = Field(foreign_key=USUARIOS_ID)

    # Preenchidos apenas quando o registro é editado.
    atualizado_em: datetime | None = None
    atualizado_por: int | None = Field(default=None, foreign_key=USUARIOS_ID)

    # Exclusão lógica: o registro continua no banco para preservar o histórico.
    excluido_em: datetime | None = None
    excluido_por: int | None = Field(default=None, foreign_key=USUARIOS_ID)