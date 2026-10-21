"""Conexão com o MySQL, que fica em um servidor remoto acessado por túnel SSH.

As tabelas NÃO são criadas por aqui (nada de SQLModel.metadata.create_all):
o script SQL da pasta database/ é a fonte da verdade do schema, com regras
(CHECK, colunas geradas, índices únicos) que o ORM não reproduz. Os modelos
apenas espelham o que já existe no banco.
"""
from collections.abc import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine
from sshtunnel import SSHTunnelForwarder

from app.core.config import get_settings

# Estado único da aplicação: um túnel e um engine, criados na inicialização.
_tunel: SSHTunnelForwarder | None = None
_engine: Engine | None = None


def _usar_utc(dbapi_connection, _connection_record) -> None:
    # O schema grava as datas em UTC (DEFAULT CURRENT_TIMESTAMP usa o fuso da
    # sessão). Fixar UTC aqui impede que o fuso do servidor MySQL altere os
    # horários de entrada e saída, que definem o valor cobrado.
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET time_zone = '+00:00'")
    finally:
        cursor.close()


def iniciar_conexao() -> Engine:
    """Abre o túnel SSH e cria o engine. É seguro chamar mais de uma vez."""
    global _tunel, _engine
    if _engine is not None:
        return _engine

    settings = get_settings()
    tunel = SSHTunnelForwarder(
        (settings.ssh_host, settings.ssh_port),
        ssh_username=settings.ssh_user,
        ssh_password=settings.ssh_password.get_secret_value(),
        remote_bind_address=(settings.db_host, settings.db_port),
        # Porta 0: o sistema operacional escolhe uma porta local livre. Evita
        # conflito com outro túnel ou MySQL já aberto neste computador.
        local_bind_address=("127.0.0.1", 0),
        # Autenticação só por senha: impede que o programa tente usar chaves
        # ou o agente SSH do computador e falhe por causa delas.
        allow_agent=False,
        host_pkey_directories=[],
        # Sem tráfego, firewalls costumam derrubar o túnel. O keepalive
        # mantém a conexão aberta entre uma requisição e outra.
        set_keepalive=30.0,
    )
    # Observação: a chave do servidor SSH não é verificada (ssh_host_key).
    # Aceitável em rede interna de estudo; em produção deve ser configurada,
    # para não conectar em um servidor falso.
    tunel.start()

    engine = create_engine(
        settings.database_url(tunel.local_bind_port),
        # Testa a conexão antes de usá-la: o MySQL derruba conexões ociosas e,
        # sem isso, a primeira requisição depois de um tempo parado falharia.
        pool_pre_ping=True,
        pool_recycle=1800,
    )
    event.listen(engine, "connect", _usar_utc)

    _tunel, _engine = tunel, engine
    return engine


def encerrar_conexao() -> None:
    """Fecha as conexões do banco e o túnel SSH."""
    global _tunel, _engine
    if _engine is not None:
        _engine.dispose()
    if _tunel is not None:
        _tunel.stop()
    _tunel = _engine = None


def get_session() -> Generator[Session, None, None]:
    # Uma sessão por requisição; o "with" garante o fechamento mesmo em erro.
    if _engine is None:
        raise RuntimeError("Conexão não iniciada: chame iniciar_conexao() na subida da aplicação.")
    with Session(_engine) as session:
        yield session