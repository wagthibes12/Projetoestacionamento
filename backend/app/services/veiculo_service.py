
"""Regras de negócio para o cadastro de veículos."""

from sqlmodel import Session

from app.models.base import agora_utc
from app.models.veiculo import Veiculo
from app.repositories import cliente_repository, veiculo_repository
from app.schemas.veiculo import VeiculoCriar, VeiculoAtualizar


class VeiculoNaoEncontrado(Exception):
    pass


class PlacaDuplicada(Exception):
    pass


class ClienteVeiculoInvalido(Exception):
    pass


def listar_veiculos(
    session: Session,
    limite: int = 100,
    deslocamento: int = 0,
) -> list[Veiculo]:
    """Lista veículos não excluídos."""
    return veiculo_repository.listar(session, limite, deslocamento)


def buscar_veiculo(session: Session, veiculo_id: int) -> Veiculo:
    """Busca um veículo pelo ID."""
    veiculo = veiculo_repository.buscar_por_id(session, veiculo_id)

    if veiculo is None:
        raise VeiculoNaoEncontrado()

    return veiculo


def validar_cliente(
    session: Session,
    cliente_id: int | None,
) -> None:
    """Confere se o cliente vinculado existe e está ativo."""

    if cliente_id is None:
        return

    cliente = cliente_repository.buscar_por_id(session, cliente_id)

    if cliente is None or not cliente.ativo:
        raise ClienteVeiculoInvalido()


def criar_veiculo(
    session: Session,
    dados: VeiculoCriar,
    usuario_id: int,
) -> Veiculo:
    """Valida e cadastra um veículo."""

    if veiculo_repository.buscar_por_placa(session, dados.placa):
        raise PlacaDuplicada()

    validar_cliente(session, dados.cliente_id)

    veiculo = Veiculo(
        **dados.model_dump(),
        criado_por=usuario_id,
    )

    return veiculo_repository.criar(session, veiculo)


def atualizar_veiculo(
    session: Session,
    veiculo_id: int,
    dados: VeiculoAtualizar,
    usuario_id: int,
) -> Veiculo:
    """Atualiza somente os campos enviados."""

    veiculo = buscar_veiculo(session, veiculo_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "placa" in alteracoes and alteracoes["placa"] is None:
        raise ValueError("A placa não pode ser nula.")

    nova_placa = alteracoes.get("placa")

    if nova_placa is not None:
        existente = veiculo_repository.buscar_por_placa(
            session,
            nova_placa,
        )

        if existente is not None and existente.id != veiculo.id:
            raise PlacaDuplicada()

    if "cliente_id" in alteracoes:
        validar_cliente(session, alteracoes["cliente_id"])

    for campo, valor in alteracoes.items():
        setattr(veiculo, campo, valor)

    veiculo.atualizado_em = agora_utc()
    veiculo.atualizado_por = usuario_id

    return veiculo_repository.salvar(session, veiculo)


def excluir_veiculo(
    session: Session,
    veiculo_id: int,
    usuario_id: int,
) -> None:
    """Realiza a exclusão lógica do veículo."""

    veiculo = buscar_veiculo(session, veiculo_id)

    veiculo.ativo = False
    veiculo.excluido_em = agora_utc()
    veiculo.excluido_por = usuario_id

    veiculo_repository.salvar(session, veiculo)
