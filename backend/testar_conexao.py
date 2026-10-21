"""Teste manual da conexão com o banco.

Uso (dentro da pasta backend, com o .venv ativo):
    python testar_conexao.py
"""
from sqlalchemy import text

from app.core.database import encerrar_conexao, iniciar_conexao

TABELAS_ESPERADAS = {
    "usuarios_estacionamento",
    "clientes_estacionamento",
    "veiculos_estacionamento",
    "vagas",
    "precos",
    "mensalistas",
    "movimentacoes",
    "mensalidades",
}


def main() -> None:
    print("Abrindo túnel SSH e conectando ao MySQL...")
    engine = iniciar_conexao()
    try:
        with engine.connect() as conn:
            banco, versao = conn.execute(text("SELECT DATABASE(), VERSION()")).one()
            tabelas = set(conn.execute(text("SHOW TABLES")).scalars().all())
        print(f"Conectado ao banco '{banco}' (MySQL {versao}).")

        faltando = TABELAS_ESPERADAS - tabelas
        if faltando:
            print("Tabelas do projeto que NÃO foram encontradas:", ", ".join(sorted(faltando)))
        else:
            print("As 8 tabelas do projeto foram encontradas.")
    finally:
        # Fecha o túnel mesmo se algo falhar, para o programa terminar limpo.
        encerrar_conexao()


if __name__ == "__main__":
    main()