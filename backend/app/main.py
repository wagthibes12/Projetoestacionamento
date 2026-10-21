import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.core.database import encerrar_conexao, get_session, iniciar_conexao

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # O túnel SSH e o engine são abertos uma única vez, na subida da API, e
    # fechados no desligamento. Se a conexão falhar, a aplicação nem sobe, e o
    # erro aparece logo no terminal em vez de estourar na primeira requisição.
    iniciar_conexao()
    yield
    encerrar_conexao()


app = FastAPI(title="Controle de Estacionamento", lifespan=lifespan)


@app.get("/saude/banco", tags=["Saúde"])
def verificar_banco(session: Session = Depends(get_session)) -> dict:
    """Confirma que a API consegue falar com o banco de dados."""
    try:
        banco, versao = session.connection().execute(
            text("SELECT DATABASE(), VERSION()")
        ).one()
    except SQLAlchemyError:
        # O detalhe vai só para o log; a resposta não expõe host, usuário
        # nem senha.
        logger.exception("Falha ao consultar o banco de dados")
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")
    return {"status": "ok", "banco": banco, "versao_servidor": versao}