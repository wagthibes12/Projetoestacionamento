"""Teste manual do hash de senha e do token de login (não usa o banco).

Uso (dentro da pasta backend, com o .venv ativo):
    python testar_seguranca.py
"""
from app.core.security import (
    criar_token_acesso,
    gerar_hash_senha,
    ler_token_acesso,
    verificar_senha,
)


def conferir(descricao: str, condicao: bool) -> None:
    print(("OK      " if condicao else "FALHOU  ") + descricao)


def main() -> None:
    senha = "Senha@Teste123"
    senha_hash = gerar_hash_senha(senha)
    conferir("o hash não contém a senha em texto puro", senha not in senha_hash)
    conferir("senha correta é aceita", verificar_senha(senha, senha_hash))
    conferir("senha errada é recusada", not verificar_senha("outra-senha", senha_hash))
    conferir("hash inválido é recusado sem erro", not verificar_senha(senha, "lixo"))

    token = criar_token_acesso(42)
    conferir("token válido devolve o id do operador", ler_token_acesso(token) == 42)

    cabecalho, corpo, assinatura = token.split(".")
    adulterado = ".".join([cabecalho, corpo, "A" * len(assinatura)])
    conferir("token com assinatura adulterada é recusado", ler_token_acesso(adulterado) is None)
    conferir("texto qualquer não é aceito como token", ler_token_acesso("lixo") is None)


if __name__ == "__main__":
    main()