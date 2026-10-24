
"""Regras de negócio para o cadastro de clientes."""
from datetime import datetime, timezone

from sqlmodel import Session

from app.models.cliente import Cliente
from app.repositories import cliente_repository
from app.schemas.cliente import ClienteCriar, ClienteAtualizar


class ClienteNaoEncontrado(Exception):
    pass


class DocumentoDuplicado(Exception):
    pass


def agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def listar_clientes(
    session: Session,
    limite: int = 100,
    deslocamento: int = 0,
) -> list[Cliente]:
    return cliente_repository.listar(session, limite, deslocamento)


def buscar_cliente(session: Session, cliente_id: int) -> Cliente:
    cliente = cliente_repository.buscar_por_id(session, cliente_id)
    if cliente is None:
        raise ClienteNaoEncontrado()
    return cliente


def criar_cliente(
    session: Session,
    dados: ClienteCriar,
    usuario_id: int,
) -> Cliente:
    documento = dados.cpf_cnpj

    if cliente_repository.buscar_por_cpf_cnpj(session, documento):
        raise DocumentoDuplicado()

    cliente = Cliente(
        **dados.model_dump(),
        criado_por=usuario_id,
    )
    return cliente_repository.criar(session, cliente)


def atualizar_cliente(
    session: Session,
    cliente_id: int,
    dados: ClienteAtualizar,
    usuario_id: int,
) -> Cliente:
    cliente = buscar_cliente(session, cliente_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    # Campos obrigatórios não podem ser apagados com null.
    for campo in ("nome", "cpf_cnpj"):
        if campo in alteracoes and alteracoes[campo] is None:
            raise ValueError(f"O campo {campo} não pode ser nulo.")

    novo_documento = alteracoes.get("cpf_cnpj")
    if novo_documento is not None:
        existente = cliente_repository.buscar_por_cpf_cnpj(
            session, novo_documento
        )
        if existente is not None and existente.id != cliente.id:
            raise DocumentoDuplicado()

    for campo, valor in alteracoes.items():
        setattr(cliente, campo, valor)

    cliente.atualizado_em = agora_utc()
    cliente.atualizado_por = usuario_id

    return cliente_repository.salvar(session, cliente)


def excluir_cliente(
    session: Session,
    cliente_id: int,
    usuario_id: int,
) -> None:
    cliente = buscar_cliente(session, cliente_id)

    cliente.ativo = False
    cliente.excluido_em = agora_utc()
    cliente.excluido_por = usuario_id

    cliente_repository.salvar(session, cliente)
