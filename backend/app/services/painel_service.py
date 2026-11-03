"""Monta o painel de vagas: o que está livre, ocupado ou reservado agora."""
from sqlmodel import Session, col, select

from app.models import Mensalista, Movimentacao, Vaga, Veiculo
from app.models.enums import StatusMovimentacao
from app.schemas.operacao import PainelSaida, VagaPainel


def montar_painel(session: Session) -> PainelSaida:
    vagas = session.exec(
        select(Vaga)
        .where(col(Vaga.ativa).is_(True), col(Vaga.excluido_em).is_(None))
        .order_by(col(Vaga.id))
    ).all()

    # Veículos estacionados agora, indexados pela vaga que ocupam.
    ocupadas = {
        movimentacao.vaga_id: (movimentacao, placa)
        for movimentacao, placa in session.exec(
            select(Movimentacao, Veiculo.placa)
            .join(Veiculo, col(Veiculo.id) == Movimentacao.veiculo_id)
            .where(
                Movimentacao.status == StatusMovimentacao.ABERTA,
                col(Movimentacao.excluido_em).is_(None),
            )
        ).all()
    }

    # Vagas com contrato de mensalista vigente, mesmo que o dono não esteja nelas.
    reservadas = {
        vaga_id: placa
        for vaga_id, placa in session.exec(
            select(Mensalista.vaga_id, Veiculo.placa)
            .join(Veiculo, col(Veiculo.id) == Mensalista.veiculo_id)
            .where(col(Mensalista.ativo).is_(True), col(Mensalista.excluido_em).is_(None))
        ).all()
    }

    itens: list[VagaPainel] = []
    for vaga in vagas:
        if vaga.id in ocupadas:
            movimentacao, placa = ocupadas[vaga.id]
            itens.append(
                VagaPainel(
                    vaga_id=vaga.id,
                    codigo=vaga.codigo,
                    situacao="OCUPADA",
                    placa=placa,
                    tipo=movimentacao.tipo,
                    movimentacao_id=movimentacao.id,
                    entrada_em=movimentacao.entrada_em,
                )
            )
        elif vaga.id in reservadas:
            itens.append(
                VagaPainel(
                    vaga_id=vaga.id,
                    codigo=vaga.codigo,
                    situacao="RESERVADA",
                    placa=reservadas[vaga.id],
                )
            )
        else:
            itens.append(VagaPainel(vaga_id=vaga.id, codigo=vaga.codigo, situacao="LIVRE"))

    return PainelSaida(
        total=len(itens),
        livres=sum(1 for i in itens if i.situacao == "LIVRE"),
        ocupadas=sum(1 for i in itens if i.situacao == "OCUPADA"),
        reservadas=sum(1 for i in itens if i.situacao == "RESERVADA"),
        vagas=itens,
    )