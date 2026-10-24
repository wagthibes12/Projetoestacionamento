
"""Schemas de entrada e saída para clientes."""

import re

from pydantic import ConfigDict, EmailStr, field_validator
from sqlmodel import SQLModel


def validar_cpf_cnpj(valor: str) -> str:
    """Remove a formatação e valida os dígitos verificadores do CPF/CNPJ."""
    documento = re.sub(r"\D", "", valor)

    # Validação de CPF
    if len(documento) == 11:
        if documento == documento[0] * 11:
            raise ValueError("CPF inválido.")

        numeros = [int(d) for d in documento]

        soma = sum(numeros[i] * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10

        soma = sum(numeros[i] * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10

        if numeros[9] != digito1 or numeros[10] != digito2:
            raise ValueError("CPF inválido.")

    # Validação de CNPJ
    elif len(documento) == 14:
        if documento == documento[0] * 14:
            raise ValueError("CNPJ inválido.")

        numeros = [int(d) for d in documento]

        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(numeros[i] * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(numeros[i] * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        if numeros[12] != digito1 or numeros[13] != digito2:
            raise ValueError("CNPJ inválido.")

    else:
        raise ValueError(
            "Informe um CPF com 11 ou CNPJ com 14 dígitos."
        )

    return documento


class ClienteCriar(SQLModel):
    """Dados necessários para cadastrar um cliente."""

    nome: str
    cpf_cnpj: str
    telefone: str | None = None
    email: EmailStr | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = valor.strip()

        if not valor:
            raise ValueError("O nome é obrigatório.")

        if len(valor) > 150:
            raise ValueError("O nome deve ter no máximo 150 caracteres.")

        return valor

    @field_validator("cpf_cnpj")
    @classmethod
    def validar_documento(cls, valor: str) -> str:
        return validar_cpf_cnpj(valor)

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()

            if len(valor) > 20:
                raise ValueError(
                    "O telefone deve ter no máximo 20 caracteres."
                )

            return valor or None

        return valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: EmailStr | None) -> EmailStr | None:
        if valor is not None and len(str(valor)) > 150:
            raise ValueError("O e-mail deve ter no máximo 150 caracteres.")

        return valor


class ClienteAtualizar(SQLModel):
    """Dados permitidos na atualização de um cliente."""

    nome: str | None = None
    cpf_cnpj: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    ativo: bool | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()

            if not valor:
                raise ValueError("O nome é obrigatório.")

            if len(valor) > 150:
                raise ValueError("O nome deve ter no máximo 150 caracteres.")

        return valor

    @field_validator("cpf_cnpj")
    @classmethod
    def validar_documento(cls, valor: str | None) -> str | None:
        if valor is not None:
            return validar_cpf_cnpj(valor)

        return valor

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()

            if len(valor) > 20:
                raise ValueError(
                    "O telefone deve ter no máximo 20 caracteres."
                )

            return valor or None

        return valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: EmailStr | None) -> EmailStr | None:
        if valor is not None and len(str(valor)) > 150:
            raise ValueError("O e-mail deve ter no máximo 150 caracteres.")

        return valor


class ClienteResposta(SQLModel):
    """Formato dos dados devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str
    telefone: str | None
    email: str | None
    ativo: bool
