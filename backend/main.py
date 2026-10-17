from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, SQLModel, Field
from datetime import datetime
from typing import Optional

from app.core.database import get_session, engine

app = FastAPI(title="Sistema de Estacionamento")

# --- MODELO DA VAGA (Baseado no seu Schema) ---
class Vaga(SQLModel, table=True):
    __tablename__ = "vagas"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True, max_length=10)
    ativa: int = Field(default=1)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    criado_por: int = Field(default=1)  # Temporariamente fixo no usuário 1 até termos autenticação
    atualizado_em: Optional[datetime] = Field(default=None)
    atualizado_por: Optional[int] = Field(default=None)
    excluido_em: Optional[datetime] = Field(default=None)
    excluido_por: Optional[int] = Field(default=None)

# Cria a tabela no banco automaticamente ao iniciar (caso não exista)
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def read_root():
    return {"mensagem": "API de Estacionamento online!"}

# --- ENDPOINTS DE VAGAS ---

@app.post("/vagas/", response_model=Vaga)
def criar_vaga(codigo: str, session: Session = Depends(get_session)):
    """Cadastra uma nova vaga no estacionamento."""
    # Verifica se a vaga já existe
    existing_vaga = session.exec(select(Vaga).where(Vaga.codigo == codigo)).first()
    if existing_vaga:
        raise HTTPException(status_code=400, response_detail="Esta vaga já está cadastrada.")
    
    nova_vaga = Vaga(codigo=codigo)
    session.add(nova_vaga)
    session.commit()
    session.refresh(nova_vaga)
    return nova_vaga

@app.get("/vagas/", response_model=list[Vaga])
def listar_vagas(session: Session = Depends(get_session)):
    """Lista todas as vagas cadastradas."""
    vagas = session.exec(select(Vaga).where(Vaga.excluido_em == None)).all()
    return vagas