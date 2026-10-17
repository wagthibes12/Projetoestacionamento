from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Parâmetros SSH
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str
    ssh_password: SecretStr

    # Parâmetros do Banco de Dados
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: SecretStr

@lru_cache()
def get_settings() -> Settings:
    return Settings()