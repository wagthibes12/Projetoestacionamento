"""Modelo da tabela usuarios_estacionamento (operadores do sistema)."""
from sqlmodel import Field

from app.models.base import USUARIOS_ID, AuditoriaBase


class Usuario(AuditoriaBase, table=True):
    __tablename__ = "usuarios_estacionamento"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=100)
    # Espelha o índice único do banco. O login continua reservado mesmo após
    # a exclusão lógica, para ninguém "herdar" a identidade no histórico.
    login: str = Field(max_length=50, unique=True)
    # Somente o hash (bcrypt/argon2); a senha em texto puro nunca é guardada.
    senha_hash: str = Field(max_length=255)
    ativo: bool = Field(default=True)

    # Nesta tabela o autor pode ser nulo: o primeiro operador (criado na
    # instalação) não tem quem o tenha criado. Nas demais tabelas é obrigatório.
    criado_por: int | None = Field(default=None, foreign_key=USUARIOS_ID)