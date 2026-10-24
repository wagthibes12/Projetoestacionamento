"""Cria o primeiro operador do sistema (instalação inicial).

Uso (dentro da pasta backend, com o .venv ativo):
    python criar_primeiro_operador.py

Só funciona enquanto a tabela estiver vazia. Os demais operadores serão
cadastrados pela própria API, por um operador já autenticado.
A senha é pedida no terminal e não fica gravada em arquivo nenhum.
"""
from getpass import getpass

from sqlmodel import Session

from app.core.database import encerrar_conexao, iniciar_conexao
from app.core.security import gerar_hash_senha
from app.models import Usuario
from app.repositories import usuario_repository

TAMANHO_MINIMO_SENHA = 8


def main() -> None:
    engine = iniciar_conexao()
    try:
        with Session(engine) as session:
            if usuario_repository.existe_algum(session):
                print("Já existe operador cadastrado. Nada foi alterado.")
                return

            nome = input("Nome do operador: ").strip()
            # Login sempre em minúsculas, para "Maria" e "maria" não virarem
            # dois cadastros diferentes.
            login = input("Login (3 a 50 caracteres, sem espaços): ").strip().lower()
            senha = getpass("Senha (não aparece enquanto você digita): ")
            confirmacao = getpass("Repita a senha: ")

            if not nome:
                print("O nome é obrigatório. Nada foi gravado.")
                return
            if not 3 <= len(login) <= 50 or " " in login:
                print("Login inválido: use de 3 a 50 caracteres, sem espaços. Nada foi gravado.")
                return
            if len(senha) < TAMANHO_MINIMO_SENHA:
                print(f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres. Nada foi gravado.")
                return
            if senha != confirmacao:
                print("As senhas não conferem. Nada foi gravado.")
                return

            # criado_por fica vazio: o primeiro operador não tem quem o tenha criado.
            usuario = Usuario(nome=nome, login=login, senha_hash=gerar_hash_senha(senha))
            usuario = usuario_repository.criar(session, usuario)
            print(f"Operador '{usuario.login}' criado com sucesso (id {usuario.id}).")
    finally:
        encerrar_conexao()


if __name__ == "__main__":
    main()