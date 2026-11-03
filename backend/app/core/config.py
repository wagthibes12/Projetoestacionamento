"""Configurações da aplicação, lidas do arquivo .env."""
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

# O .env é localizado a partir deste arquivo, e não do diretório em que o
# terminal está aberto, para funcionar igual rodando da raiz do projeto ou
# de dentro da pasta backend.
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Túnel SSH (opcional): só é usado quando SSH_HOST está preenchido. Sem
    # ele, a aplicação conecta direto no banco, em DB_HOST:DB_PORT.
    ssh_host: str | None = None
    ssh_port: int = 22
    ssh_user: str | None = None
    # SecretStr impede que as senhas apareçam por engano em logs e no repr().
    ssh_password: SecretStr | None = None

    # Banco de dados. Com túnel SSH, são o host e a porta do banco como o
    # servidor SSH os enxerga (normalmente 127.0.0.1 e 3306).
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: SecretStr

    # Autenticação. A chave NÃO tem valor padrão de propósito: um padrão
    # conhecido permitiria a qualquer pessoa forjar tokens de login.
    secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    # Duração do login. 480 minutos = um turno de 8 horas.
    access_token_minutes: int = 480

    @property
    def usa_tunel_ssh(self) -> bool:
        return bool(self.ssh_host)

    def database_url(self, host: str, porta: int) -> URL:
        # URL.create escapa caracteres especiais: com f-string, uma senha com
        # "@" ou "/" quebraria a URL.
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=host,
            port=porta,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    # Em cache para o .env ser lido uma única vez. Se faltar alguma variável
    # obrigatória, o erro aparece já na inicialização, e não só na primeira
    # requisição.
    return Settings()