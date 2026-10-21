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

    # Túnel SSH: o MySQL fica em um servidor remoto, acessado por SSH.
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str
    # SecretStr impede que as senhas apareçam por engano em logs e no repr().
    ssh_password: SecretStr

    # Banco de dados, como o servidor SSH enxerga (por isso 127.0.0.1).
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: SecretStr

    def database_url(self, porta_local: int) -> URL:
        # A porta local do túnel só é conhecida depois que ele abre, por isso
        # a URL é montada sob demanda. URL.create escapa caracteres especiais:
        # com f-string, uma senha com "@" ou "/" quebraria a URL.
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host="127.0.0.1",
            port=porta_local,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    # Em cache para o .env ser lido uma única vez. Se faltar alguma variável
    # obrigatória, o erro aparece já na inicialização, e não só na primeira
    # requisição.
    return Settings()