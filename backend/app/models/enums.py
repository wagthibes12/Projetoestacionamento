"""Valores fixos (ENUM) usados nas tabelas.

Os nomes dos membros são idênticos aos valores do banco, porque o SQLAlchemy
grava e lê o NOME do membro nas colunas ENUM.
"""
from enum import StrEnum


class TipoVeiculo(StrEnum):
    CARRO = "CARRO"
    MOTO = "MOTO"
    OUTRO = "OUTRO"


class TipoCobranca(StrEnum):
    HORISTA = "HORISTA"
    MENSALISTA = "MENSALISTA"


class FormaPagamento(StrEnum):
    DINHEIRO = "DINHEIRO"
    PIX = "PIX"
    CARTAO = "CARTAO"


class StatusMovimentacao(StrEnum):
    ABERTA = "ABERTA"
    FINALIZADA = "FINALIZADA"


class StatusMensalidade(StrEnum):
    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    CANCELADA = "CANCELADA"