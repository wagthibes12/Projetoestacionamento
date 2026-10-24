"""Confere se os modelos batem com as tabelas reais do banco.

Uso (dentro da pasta backend, com o .venv ativo):
    python testar_modelos.py

Para cada modelo, o SQLModel faz um SELECT com todas as colunas que ele
declara. Se alguma coluna não existir no banco (ou tiver nome diferente),
o banco responde com erro "Unknown column", e o problema aparece aqui.
"""
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import encerrar_conexao, iniciar_conexao
from app.models import (
    Cliente,
    Mensalidade,
    Mensalista,
    Movimentacao,
    Preco,
    Usuario,
    Vaga,
    Veiculo,
)

# Cada novo modelo criado entra nesta lista.
MODELOS = [Usuario, Cliente, Veiculo, Vaga, Preco, Mensalista, Movimentacao, Mensalidade]


def main() -> None:
    engine = iniciar_conexao()
    try:
        with Session(engine) as session:
            for modelo in MODELOS:
                session.exec(select(modelo).limit(1)).first()
                total = session.exec(select(func.count()).select_from(modelo)).one()
                print(f"OK  {modelo.__tablename__}: colunas conferem ({total} registros)")
    finally:
        encerrar_conexao()


if __name__ == "__main__":
    main()