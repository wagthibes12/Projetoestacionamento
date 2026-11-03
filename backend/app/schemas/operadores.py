"""Formato dos dados do cadastro de operadores.

A senha só entra: nenhum formato de saída traz a senha nem o hash dela.
"""
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.comum import SaidaBase

NomeOperador = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
# Login sempre em minúsculas e sem espaços, para "Maria" e "maria" não virarem
# dois cadastros diferentes.
LoginOperador = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, min_length=3, max_length=50, pattern=r"^\S+$"),
]


class OperadorEntrada(BaseModel):
    nome: NomeOperador
    login: LoginOperador
    senha: str = Field(min_length=8, max_length=128)


class OperadorAtualizacao(BaseModel):
    nome: NomeOperador | None = None
    senha: str | None = Field(default=None, min_length=8, max_length=128)
    ativo: bool | None = None


class OperadorSaida(SaidaBase):
    nome: str
    login: str
    ativo: bool