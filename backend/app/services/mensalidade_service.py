"""Regras de negócio das mensalidades dos mensalistas."""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models import Cliente, Mensalidade, Mensalista, Usuario, Vaga, Veiculo
from app.models.base import agora_utc
from app.models.enums import FormaPagamento, StatusMensalidade
from app.schemas.mensalidades import GerarSaida, MensalidadeDetalhe


def _consulta_detalhes():
    # Uma única consulta traz a mensalidade junto com o nome do cliente, a placa
    # e o código da vaga do contrato.
    return (
        select(Mensalidade, Cliente.nome, Veiculo.placa, Vaga.codigo)
        .join(Mensalista, col(Mensalista.id) == Mensalidade.mensalista_id)
        .join(Cliente, col(Cliente.id) == Mensalista.cliente_id)
        .join(Veiculo, col(Veiculo.id) == Mensalista.veiculo_id)
        .join(Vaga, col(Vaga.id) == Mensalista.vaga_id)
        .where(col(Mensalidade.excluido_em).is_(None))
    )


def _para_detalhe(mensalidade: Mensalidade, cliente_nome: str, placa: str, codigo_vaga: str) -> MensalidadeDetalhe:
    return MensalidadeDetalhe(
        id=mensalidade.id,
        mensalista_id=mensalidade.mensalista_id,
        cliente_nome=cliente_nome,
        placa=placa,
        vaga_codigo=codigo_vaga,
        competencia=mensalidade.competencia,
        valor=mensalidade.valor,
        vencimento=mensalidade.vencimento,
        status=mensalidade.status,
        pago_em=mensalidade.pago_em,
        forma_pagamento=mensalidade.forma_pagamento,
    )


def _primeiro_dia(competencia: str) -> date:
    ano, mes = competencia.split("-")
    try:
        return date(int(ano), int(mes), 1)
    except ValueError:
        raise HTTPException(status_code=422, detail="Competência inválida. Use o formato AAAA-MM.")


def _detalhe_por_id(session: Session, mensalidade_id: int) -> MensalidadeDetalhe:
    linha = session.exec(_consulta_detalhes().where(col(Mensalidade.id) == mensalidade_id)).first()
    if linha is None:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada.")
    return _para_detalhe(*linha)


def _buscar(session: Session, mensalidade_id: int) -> Mensalidade:
    mensalidade = session.exec(
        select(Mensalidade).where(
            col(Mensalidade.id) == mensalidade_id,
            col(Mensalidade.excluido_em).is_(None),
        )
    ).first()
    if mensalidade is None:
        raise HTTPException(status_code=404, detail="Mensalidade não encontrada.")
    return mensalidade


def gerar(session: Session, usuario: Usuario, competencia: str) -> GerarSaida:
    """Gera a mensalidade do mês para cada contrato ativo que ainda não tem uma.

    Pode ser repetida sem risco: quem já tem a mensalidade daquele mês é pulado.
    """
    primeiro_dia = _primeiro_dia(competencia)
    contratos = session.exec(
        select(Mensalista).where(
            col(Mensalista.ativo).is_(True),
            col(Mensalista.excluido_em).is_(None),
        )
    ).all()
    # Considera também as mensalidades excluídas: o índice único do banco
    # (contrato + mês) vale para todas, e gerar de novo falharia.
    existentes = set(
        session.exec(
            select(Mensalidade.mensalista_id).where(col(Mensalidade.competencia) == primeiro_dia)
        ).all()
    )
    criadas = 0
    for contrato in contratos:
        if contrato.id in existentes:
            continue
        session.add(
            Mensalidade(
                mensalista_id=contrato.id,
                competencia=primeiro_dia,
                valor=contrato.valor_mensal,
                vencimento=primeiro_dia.replace(day=contrato.dia_vencimento),
                criado_por=usuario.id,
            )
        )
        criadas += 1
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="As mensalidades deste mês acabaram de ser geradas por outra operação. Tente de novo.",
        )
    return GerarSaida(competencia=primeiro_dia, criadas=criadas, ja_existiam=len(contratos) - criadas)


def listar(
    session: Session, competencia: str | None, status: StatusMensalidade | None
) -> list[MensalidadeDetalhe]:
    consulta = _consulta_detalhes()
    if competencia is not None:
        consulta = consulta.where(col(Mensalidade.competencia) == _primeiro_dia(competencia))
    if status is not None:
        consulta = consulta.where(Mensalidade.status == status)
    consulta = consulta.order_by(col(Mensalidade.competencia).desc(), col(Mensalidade.id))
    return [_para_detalhe(*linha) for linha in session.exec(consulta).all()]


def pagar(
    session: Session, usuario: Usuario, mensalidade_id: int, forma_pagamento: FormaPagamento
) -> MensalidadeDetalhe:
    mensalidade = _buscar(session, mensalidade_id)
    if mensalidade.status != StatusMensalidade.PENDENTE:
        raise HTTPException(
            status_code=409, detail=f"A mensalidade já está {mensalidade.status.value.lower()}."
        )
    agora = agora_utc()
    mensalidade.status = StatusMensalidade.PAGA
    mensalidade.pago_em = agora
    mensalidade.forma_pagamento = forma_pagamento
    mensalidade.recebido_por = usuario.id
    mensalidade.atualizado_em = agora
    mensalidade.atualizado_por = usuario.id
    session.commit()
    return _detalhe_por_id(session, mensalidade_id)


def cancelar(session: Session, usuario: Usuario, mensalidade_id: int) -> MensalidadeDetalhe:
    mensalidade = _buscar(session, mensalidade_id)
    if mensalidade.status != StatusMensalidade.PENDENTE:
        raise HTTPException(
            status_code=409,
            detail=f"Só é possível cancelar mensalidade pendente. Esta já está {mensalidade.status.value.lower()}.",
        )
    mensalidade.status = StatusMensalidade.CANCELADA
    mensalidade.atualizado_em = agora_utc()
    mensalidade.atualizado_por = usuario.id
    session.commit()
    return _detalhe_por_id(session, mensalidade_id)


def excluir(session: Session, usuario: Usuario, mensalidade_id: int) -> None:
    """Exclusão lógica, para corrigir uma mensalidade gerada por engano."""
    mensalidade = _buscar(session, mensalidade_id)
    mensalidade.excluido_em = agora_utc()
    mensalidade.excluido_por = usuario.id
    session.commit()