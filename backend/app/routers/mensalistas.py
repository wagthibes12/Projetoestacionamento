"""Rotas dos contratos de mensalistas (cliente + veículo + vaga fixa)."""
from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.models import Cliente, Mensalista, Movimentacao, Preco, Usuario, Vaga, Veiculo
from app.models.enums import StatusMovimentacao, TipoCobranca
from app.routers.crud_base import criar_router_crud
from app.schemas.mensalistas import MensalistaAtualizacao, MensalistaEntrada, MensalistaSaida


def _preparar_contrato(session: Session, usuario: Usuario, dados: MensalistaEntrada) -> None:
    """Confere as regras do contrato antes de gravar e preenche o valor mensal.

    O banco já impede, por índice único, dois contratos ativos para a mesma vaga
    ou o mesmo veículo. As conferências abaixo existem para devolver uma
    mensagem clara ao operador, em vez de um erro genérico de conflito.
    """
    cliente = session.exec(
        select(Cliente).where(
            col(Cliente.id) == dados.cliente_id,
            col(Cliente.ativo).is_(True),
            col(Cliente.excluido_em).is_(None),
        )
    ).first()
    if cliente is None:
        raise HTTPException(status_code=422, detail="Cliente não encontrado ou inativo.")

    veiculo = session.exec(
        select(Veiculo).where(
            col(Veiculo.id) == dados.veiculo_id,
            col(Veiculo.ativo).is_(True),
            col(Veiculo.excluido_em).is_(None),
        )
    ).first()
    if veiculo is None:
        raise HTTPException(status_code=422, detail="Veículo não encontrado ou inativo.")
    if veiculo.cliente_id is not None and veiculo.cliente_id != dados.cliente_id:
        raise HTTPException(status_code=422, detail="Este veículo está cadastrado para outro cliente.")

    vaga = session.exec(
        select(Vaga).where(
            col(Vaga.id) == dados.vaga_id,
            col(Vaga.ativa).is_(True),
            col(Vaga.excluido_em).is_(None),
        )
    ).first()
    if vaga is None:
        raise HTTPException(status_code=422, detail="Vaga não encontrada ou inativa.")

    ocupada_agora = session.exec(
        select(Movimentacao.id).where(
            col(Movimentacao.vaga_id) == vaga.id,
            Movimentacao.status == StatusMovimentacao.ABERTA,
            col(Movimentacao.excluido_em).is_(None),
        )
    ).first()
    if ocupada_agora is not None:
        raise HTTPException(
            status_code=409,
            detail="A vaga está ocupada agora por um veículo. Aguarde a saída antes de criar o contrato.",
        )

    contrato_da_vaga = session.exec(
        select(Mensalista.id).where(
            col(Mensalista.vaga_id) == vaga.id,
            col(Mensalista.ativo).is_(True),
            col(Mensalista.excluido_em).is_(None),
        )
    ).first()
    if contrato_da_vaga is not None:
        raise HTTPException(status_code=409, detail="Esta vaga já tem um contrato ativo.")

    contrato_do_veiculo = session.exec(
        select(Mensalista.id).where(
            col(Mensalista.veiculo_id) == veiculo.id,
            col(Mensalista.ativo).is_(True),
            col(Mensalista.excluido_em).is_(None),
        )
    ).first()
    if contrato_do_veiculo is not None:
        raise HTTPException(status_code=409, detail="Este veículo já tem um contrato ativo.")

    if dados.valor_mensal is None:
        # O valor é copiado do preço vigente na assinatura: uma mudança futura
        # de preço não altera contratos já firmados.
        preco = session.exec(
            select(Preco).where(
                Preco.tipo == TipoCobranca.MENSALISTA,
                col(Preco.ativo).is_(True),
                col(Preco.excluido_em).is_(None),
            )
        ).first()
        if preco is None:
            raise HTTPException(
                status_code=409,
                detail="Cadastre o preço do mensalista ou informe o valor_mensal.",
            )
        dados.valor_mensal = preco.valor


router_mensalistas = criar_router_crud(
    modelo=Mensalista,
    entrada=MensalistaEntrada,
    atualizacao=MensalistaAtualizacao,
    saida=MensalistaSaida,
    prefixo="/mensalistas",
    tag="Mensalistas",
    antes_de_criar=_preparar_contrato,
)