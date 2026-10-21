"""Importar todos os modelos aqui garante que o SQLAlchemy conheça todas as
tabelas. As chaves estrangeiras referenciam tabelas pelo nome; se algum modelo
não tiver sido importado, gravar um registro falha com NoReferencedTableError.
"""
from app.models.cliente import Cliente
from app.models.mensalidade import Mensalidade
from app.models.mensalista import Mensalista
from app.models.movimentacao import Movimentacao
from app.models.preco import Preco
from app.models.usuario import Usuario
from app.models.vaga import Vaga
from app.models.veiculo import Veiculo

__all__ = [
    "Cliente",
    "Mensalidade",
    "Mensalista",
    "Movimentacao",
    "Preco",
    "Usuario",
    "Vaga",
    "Veiculo",
]