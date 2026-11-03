"""Regras de negócio da entrada e saída de veículos e do cálculo da cobrança."""
import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models import Mensalista, Movimentacao, Preco, Usuario, Vaga, Veiculo
from app.models.base import agora_utc
from app.models.enums import FormaPagamento, StatusMovimentacao, TipoCobranca
from app.schemas.operacao import CobrancaSaida, EntradaPedido, MovimentacaoDetalhe


@dataclass(frozen=True)
class Cobranca:
    minutos: int
    horas_cobradas: int
    valor_hora: Decimal | None
    valor_total: Decimal


# ------------------------------------------------------------------ consultas
def _preco_horista_vigente(session: Session) -> Preco | None:
    return session.exec(
        select(Preco).where(
            Preco.tipo == TipoCobranca.HORISTA,
            col(Preco.ativo).is_(True),
            col(Preco.excluido_em).is_(None),
        )
    ).first()


def _contrato_vigente_do_veiculo(session: Session, veiculo_id: int) -> Mensalista | None:
    return session.exec(
        select(Mensalista).where(
            col(Mensalista.veiculo_id) == veiculo_id,
            col(Mensalista.ativo).is_(True),
            col(Mensalista.excluido_em).is_(None),
        )
    ).first()


def _escolher_vaga_horista(session: Session, vaga_id: int | None) -> Vaga:
    """Devolve uma vaga em que o horista pode estacionar.

    Vaga livre para horista = ativa, sem veículo estacionado agora e sem
    contrato de mensalista vigente (vaga de mensalista nunca é usada por
    horista, mesmo quando o dono não está nela).
    """
    ocupadas = select(Movimentacao.vaga_id).where(
        Movimentacao.status == StatusMovimentacao.ABERTA,
        col(Movimentacao.excluido_em).is_(None),
    )
    reservadas = select(Mensalista.vaga_id).where(
        col(Mensalista.ativo).is_(True),
        col(Mensalista.excluido_em).is_(None),
    )
    livres = (
        select(Vaga)
        .where(
            col(Vaga.ativa).is_(True),
            col(Vaga.excluido_em).is_(None),
            col(Vaga.id).not_in(ocupadas),
            col(Vaga.id).not_in(reservadas),
        )
        .order_by(col(Vaga.id))
    )
    if vaga_id is None:
        vaga = session.exec(livres.limit(1)).first()
        if vaga is None:
            raise HTTPException(status_code=409, detail="Não há vaga livre para horista no momento.")
        return vaga
    vaga = session.exec(livres.where(col(Vaga.id) == vaga_id)).first()
    if vaga is None:
        raise HTTPException(
            status_code=409,
            detail="A vaga escolhida não está disponível (inexistente, inativa, ocupada ou reservada a mensalista).",
        )
    return vaga


def _buscar_movimentacao(session: Session, movimentacao_id: int, apenas_abertas: bool) -> Movimentacao:
    consulta = select(Movimentacao).where(
        col(Movimentacao.id) == movimentacao_id,
        col(Movimentacao.excluido_em).is_(None),
    )
    if apenas_abertas:
        consulta = consulta.where(Movimentacao.status == StatusMovimentacao.ABERTA)
    movimentacao = session.exec(consulta).first()
    if movimentacao is None:
        raise HTTPException(
            status_code=404,
            detail="Entrada aberta não encontrada." if apenas_abertas else "Movimentação não encontrada.",
        )
    return movimentacao


def _para_detalhe(movimentacao: Movimentacao, placa: str, codigo_vaga: str) -> MovimentacaoDetalhe:
    return MovimentacaoDetalhe(
        id=movimentacao.id,
        tipo=movimentacao.tipo,
        veiculo_id=movimentacao.veiculo_id,
        placa=placa,
        vaga_id=movimentacao.vaga_id,
        vaga_codigo=codigo_vaga,
        entrada_em=movimentacao.entrada_em,
        saida_em=movimentacao.saida_em,
        valor_cobrado=movimentacao.valor_cobrado,
        forma_pagamento=movimentacao.forma_pagamento,
        status=movimentacao.status,
    )


def _detalhe_de(session: Session, movimentacao: Movimentacao) -> MovimentacaoDetalhe:
    veiculo = session.get(Veiculo, movimentacao.veiculo_id)
    vaga = session.get(Vaga, movimentacao.vaga_id)
    return _para_detalhe(movimentacao, veiculo.placa, vaga.codigo)


def _consulta_detalhes():
    # Uma única consulta traz a movimentação junto com a placa e o código da
    # vaga, em vez de uma consulta extra para cada linha da lista.
    return (
        select(Movimentacao, Veiculo.placa, Vaga.codigo)
        .join(Veiculo, col(Veiculo.id) == Movimentacao.veiculo_id)
        .join(Vaga, col(Vaga.id) == Movimentacao.vaga_id)
        .where(col(Movimentacao.excluido_em).is_(None))
    )


# ----------------------------------------------------------------- cobrança
def calcular_cobranca(session: Session, movimentacao: Movimentacao, ate: datetime) -> Cobranca:
    """Regra do horista: cada hora iniciada é cobrada por inteiro (mínimo de 1 hora).

    O mensalista não paga por movimentação: a cobrança dele vai pela mensalidade.
    """
    minutos = max(0, int((ate - movimentacao.entrada_em).total_seconds() // 60))
    if movimentacao.tipo == TipoCobranca.MENSALISTA:
        return Cobranca(minutos, 0, None, Decimal("0.00"))
    preco = _preco_horista_vigente(session)
    if preco is None:
        raise HTTPException(status_code=409, detail="Não há preço de horista ativo. Cadastre o preço antes.")
    horas = max(1, math.ceil(minutos / 60))
    total = (preco.valor * horas).quantize(Decimal("0.01"))
    return Cobranca(minutos, horas, preco.valor, total)


# ---------------------------------------------------------------- operações
def registrar_entrada(session: Session, usuario: Usuario, dados: EntradaPedido) -> MovimentacaoDetalhe:
    veiculo = session.exec(select(Veiculo).where(Veiculo.placa == dados.placa)).first()

    contrato = None
    if veiculo is not None:
        if veiculo.excluido_em is not None or not veiculo.ativo:
            raise HTTPException(status_code=409, detail="Este veículo está inativo ou excluído no cadastro.")
        aberta = session.exec(
            _consulta_detalhes().where(
                col(Movimentacao.veiculo_id) == veiculo.id,
                Movimentacao.status == StatusMovimentacao.ABERTA,
            )
        ).first()
        if aberta is not None:
            raise HTTPException(
                status_code=409,
                detail=f"O veículo {veiculo.placa} já está no estacionamento (vaga {aberta[2]}).",
            )
        contrato = _contrato_vigente_do_veiculo(session, veiculo.id)

    if contrato is not None:
        # Mensalista sempre usa a vaga do próprio contrato.
        tipo, vaga_id = TipoCobranca.MENSALISTA, contrato.vaga_id
    else:
        if _preco_horista_vigente(session) is None:
            raise HTTPException(
                status_code=409, detail="Cadastre o preço do horista antes de registrar entradas."
            )
        tipo, vaga_id = TipoCobranca.HORISTA, _escolher_vaga_horista(session, dados.vaga_id).id

    try:
        if veiculo is None:
            # Horista avulso: o veículo é cadastrado na primeira entrada.
            veiculo = Veiculo(placa=dados.placa, tipo=dados.tipo_veiculo, criado_por=usuario.id)
            session.add(veiculo)
            session.flush()
        movimentacao = Movimentacao(
            tipo=tipo, veiculo_id=veiculo.id, vaga_id=vaga_id, criado_por=usuario.id
        )
        session.add(movimentacao)
        session.commit()
    except IntegrityError:
        # Os índices únicos do banco impedem dois veículos na mesma vaga, ou o
        # mesmo veículo em duas vagas, mesmo com dois operadores ao mesmo tempo.
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A vaga ou o veículo acabou de ser ocupado por outra operação. Tente novamente.",
        )
    session.refresh(movimentacao)
    return _detalhe_de(session, movimentacao)


def simular_cobranca(session: Session, movimentacao_id: int) -> CobrancaSaida:
    """Mostra quanto seria cobrado agora, sem registrar a saída."""
    movimentacao = _buscar_movimentacao(session, movimentacao_id, apenas_abertas=True)
    agora = max(agora_utc(), movimentacao.entrada_em)
    cobranca = calcular_cobranca(session, movimentacao, agora)
    veiculo = session.get(Veiculo, movimentacao.veiculo_id)
    return CobrancaSaida(
        movimentacao_id=movimentacao.id,
        tipo=movimentacao.tipo,
        placa=veiculo.placa,
        entrada_em=movimentacao.entrada_em,
        calculado_em=agora,
        minutos=cobranca.minutos,
        horas_cobradas=cobranca.horas_cobradas,
        valor_hora=cobranca.valor_hora,
        valor_total=cobranca.valor_total,
    )


def registrar_saida(
    session: Session,
    usuario: Usuario,
    movimentacao_id: int,
    forma_pagamento: FormaPagamento | None,
) -> MovimentacaoDetalhe:
    movimentacao = _buscar_movimentacao(session, movimentacao_id, apenas_abertas=True)
    horista = movimentacao.tipo == TipoCobranca.HORISTA
    if horista and forma_pagamento is None:
        raise HTTPException(status_code=422, detail="Informe a forma de pagamento.")

    # Nunca antes da entrada: o banco recusa saída anterior à entrada.
    agora = max(agora_utc(), movimentacao.entrada_em)
    cobranca = calcular_cobranca(session, movimentacao, agora)

    movimentacao.saida_em = agora
    movimentacao.valor_cobrado = cobranca.valor_total
    movimentacao.forma_pagamento = forma_pagamento if horista else None
    movimentacao.status = StatusMovimentacao.FINALIZADA
    movimentacao.finalizado_por = usuario.id
    session.commit()
    session.refresh(movimentacao)
    return _detalhe_de(session, movimentacao)


def cancelar_movimentacao(session: Session, usuario: Usuario, movimentacao_id: int) -> None:
    """Exclusão lógica, para corrigir uma entrada lançada por engano.

    Se a movimentação estava aberta, a vaga e o veículo ficam livres de novo.
    """
    movimentacao = _buscar_movimentacao(session, movimentacao_id, apenas_abertas=False)
    movimentacao.excluido_em = agora_utc()
    movimentacao.excluido_por = usuario.id
    session.commit()


def listar_abertas(session: Session) -> list[MovimentacaoDetalhe]:
    consulta = _consulta_detalhes().where(Movimentacao.status == StatusMovimentacao.ABERTA)
    consulta = consulta.order_by(col(Movimentacao.entrada_em))
    return [_para_detalhe(m, placa, codigo) for m, placa, codigo in session.exec(consulta).all()]


def listar_historico(
    session: Session, status: StatusMovimentacao | None, limite: int, deslocamento: int
) -> list[MovimentacaoDetalhe]:
    consulta = _consulta_detalhes()
    if status is not None:
        consulta = consulta.where(Movimentacao.status == status)
    consulta = consulta.order_by(col(Movimentacao.id).desc()).limit(limite).offset(deslocamento)
    return [_para_detalhe(m, placa, codigo) for m, placa, codigo in session.exec(consulta).all()]