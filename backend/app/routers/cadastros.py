"""Rotas dos cadastros básicos: clientes, veículos, vagas e preços."""
from sqlmodel import Session, col, select

from app.models import Cliente, Preco, Usuario, Vaga, Veiculo
from app.models.base import agora_utc
from app.routers.crud_base import criar_router_crud
from app.schemas.cadastros import (
    ClienteAtualizacao,
    ClienteEntrada,
    ClienteSaida,
    PrecoAtualizacao,
    PrecoEntrada,
    PrecoSaida,
    VagaAtualizacao,
    VagaEntrada,
    VagaSaida,
    VeiculoAtualizacao,
    VeiculoEntrada,
    VeiculoSaida,
)


def _encerrar_preco_vigente(session: Session, usuario: Usuario, dados: PrecoEntrada) -> None:
    """Troca de preço: o preço vigente do mesmo tipo é encerrado, e o novo entra.

    O banco só aceita um preço ativo por tipo. Em vez de sobrescrever o valor
    antigo, ele é marcado como excluído, o que preserva o histórico. Tudo
    acontece na mesma transação: se o novo preço falhar, o antigo continua valendo.
    """
    if not dados.ativo:
        return
    vigentes = session.exec(
        select(Preco).where(
            Preco.tipo == dados.tipo,
            col(Preco.ativo).is_(True),
            col(Preco.excluido_em).is_(None),
        )
    ).all()
    for vigente in vigentes:
        vigente.excluido_em = agora_utc()
        vigente.excluido_por = usuario.id
        session.add(vigente)
    # Envia o encerramento ao banco antes do INSERT do preço novo, senão o
    # índice único de "um preço ativo por tipo" bloquearia a gravação.
    session.flush()


router_clientes = criar_router_crud(
    modelo=Cliente,
    entrada=ClienteEntrada,
    atualizacao=ClienteAtualizacao,
    saida=ClienteSaida,
    prefixo="/clientes",
    tag="Clientes",
)

router_veiculos = criar_router_crud(
    modelo=Veiculo,
    entrada=VeiculoEntrada,
    atualizacao=VeiculoAtualizacao,
    saida=VeiculoSaida,
    prefixo="/veiculos",
    tag="Veículos",
)

router_vagas = criar_router_crud(
    modelo=Vaga,
    entrada=VagaEntrada,
    atualizacao=VagaAtualizacao,
    saida=VagaSaida,
    prefixo="/vagas",
    tag="Vagas",
)

router_precos = criar_router_crud(
    modelo=Preco,
    entrada=PrecoEntrada,
    atualizacao=PrecoAtualizacao,
    saida=PrecoSaida,
    prefixo="/precos",
    tag="Preços",
    antes_de_criar=_encerrar_preco_vigente,
)