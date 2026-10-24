"""Formato dos dados que entram e saem da API de autenticação.

Ficam separados dos modelos de tabela para a API nunca expor, por engano,
campos internos como o hash da senha.
"""
from pydantic import BaseModel, ConfigDict, Field


class LoginEntrada(BaseModel):
    login: str = Field(min_length=1, max_length=50)
    # Limite máximo para ninguém enviar um texto gigante só para sobrecarregar
    # o cálculo do hash.
    senha: str = Field(min_length=1, max_length=128)


class TokenSaida(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioSaida(BaseModel):
    # Permite montar este formato direto a partir do modelo do banco.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    login: str