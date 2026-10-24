
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.core.database import (
    encerrar_conexao,
    get_session,
    iniciar_conexao,
)
from app.routers import auth, clientes,veiculos

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Inicia a conexão com o banco ao subir a API.
    iniciar_conexao()

    try:
        yield
    finally:
        # Encerra a conexão quando a API for desligada.
        encerrar_conexao()


app = FastAPI(
    title="Controle de Estacionamento",
    lifespan=lifespan,
)

# Permite que o frontend acesse a API durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das rotas.
app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(veiculos.router)


@app.get("/saude/banco", tags=["Saúde"])
def verificar_banco(
    session: Session = Depends(get_session),
) -> dict:
    """Confirma que a API consegue acessar o banco de dados."""

    try:
        banco, versao = session.connection().execute(
            text("SELECT DATABASE(), VERSION()")
        ).one()

    except SQLAlchemyError:
        # Não expõe detalhes da conexão na resposta ao cliente.
        logger.exception("Falha ao consultar o banco de dados")

        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponível.",
        )

    return {
        "status": "ok",
        "banco": banco,
        "versao_servidor": versao,
    }
