"""Redefine a senha de um operador (ou reativa um operador bloqueado).

Uso (dentro da pasta backend, com o .venv ativo):
    python redefinir_senha.py

Lista os operadores do banco e pede o login e a nova senha. Também reativa o
operador, caso ele esteja desativado ou excluído. A senha é pedida no terminal
e não fica gravada em arquivo nenhum.
"""
from getpass import getpass

from sqlmodel import Session, col, select

from app.core.database import encerrar_conexao, iniciar_conexao
from app.core.security import gerar_hash_senha
from app.models import Usuario
from app.models.base import agora_utc

TAMANHO_MINIMO_SENHA = 8


def main() -> None:
    engine = iniciar_conexao()
    try:
        with Session(engine) as session:
            usuarios = session.exec(select(Usuario).order_by(col(Usuario.id))).all()
            if not usuarios:
                print("Nenhum operador cadastrado neste banco.")
                print("Crie o primeiro com: python criar_primeiro_operador.py")
                return

            print("Operadores neste banco:")
            for u in usuarios:
                situacao = "excluído" if u.excluido_em else ("ativo" if u.ativo else "desativado")
                print(f"  id {u.id}: login '{u.login}' ({situacao})")

            login = input("\nLogin a redefinir: ").strip().lower()
            usuario = next((u for u in usuarios if u.login == login), None)
            if usuario is None:
                print("Esse login não está na lista acima. Nada foi alterado.")
                return

            senha = getpass("Nova senha (não aparece enquanto você digita): ")
            confirmacao = getpass("Repita a nova senha: ")
            if len(senha) < TAMANHO_MINIMO_SENHA:
                print(f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres. Nada foi alterado.")
                return
            if senha != confirmacao:
                print("As senhas não conferem. Nada foi alterado.")
                return

            usuario.senha_hash = gerar_hash_senha(senha)
            # Reativa o operador, caso estivesse bloqueado.
            usuario.ativo = True
            usuario.excluido_em = None
            usuario.excluido_por = None
            # Redefinição feita na máquina, fora da API: a autoria fica com o
            # próprio operador, para a alteração continuar registrada.
            usuario.atualizado_em = agora_utc()
            usuario.atualizado_por = usuario.id
            session.commit()
            print(f"Senha do operador '{usuario.login}' redefinida. Já pode entrar com ela.")
    finally:
        encerrar_conexao()


if __name__ == "__main__":
    main()