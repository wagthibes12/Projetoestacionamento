from urllib.parse import quote_plus
from sqlmodel import create_engine, Session
from sshtunnel import SSHTunnelForwarder
from app.core.config import get_settings

settings = get_settings()

tunnel = None
db_port = settings.db_port
db_host = settings.db_host

if settings.ssh_host:
    try:
        tunnel = SSHTunnelForwarder(
            (settings.ssh_host, settings.ssh_port),
            ssh_username=settings.ssh_user,
            ssh_password=settings.ssh_password.get_secret_value(),
            remote_bind_address=(settings.db_host, settings.db_port)
        )
        tunnel.start()
        print(f"Túnel SSH estabelecido com sucesso na porta local: {tunnel.local_bind_port}")
        
        db_port = tunnel.local_bind_port
        db_host = "127.0.0.1"
    except Exception as e:
        print(f"Erro ao estabelecer túnel SSH: {e}")

# Tratamento seguro da senha com quote_plus para evitar conflito com caracteres especiais (ex: @)
encoded_password = quote_plus(settings.db_password.get_secret_value())

DATABASE_URL = (
    f"mysql+pymysql://{settings.db_user}:{encoded_password}"
    f"@{db_host}:{db_port}/{settings.db_name}"
)

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    """Dependency para injetar a sessão do banco de dados nas rotas do FastAPI."""
    with Session(engine) as session:
        yield session