import os
import json

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, TEXT

from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

# --- Configuração do Banco de Dados ---
DATABASE_URL = f"mssql+pymssql://{os.getenv('SQL_SERVER_USER')}:{os.getenv('SQL_SERVER_PASS')}@{os.getenv('SQL_SERVER_HOST')}/{os.getenv('SQL_SERVER_DB')}"

# Cria a engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Base para os modelos declarativos
Base = declarative_base()

# --- Tipo JSON Personalizado para SQLAlchemy ---
# Isso permite armazenar e recuperar dados JSON como objetos Python
class JSONEncodedDict(TypeDecorator):
    """Armazena e recupera dicionários como strings JSON."""
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class ObrigacaoORM(Base):
    __tablename__ = "Obrigacao"

    IdObrigacao = Column(Integer, primary_key=True, index=True)
    IdProcesso = Column(Integer, nullable=False)
    IdComposicaoPauta = Column(Integer, nullable=False)
    IdVotoPauta = Column(Integer, nullable=False)
    DescricaoObrigacao = Column(Text, nullable=False)
    DeFazer = Column(Boolean, default=True)
    Prazo = Column(String, nullable=True)
    DataCumprimento = Column(Date, nullable=True)
    OrgaoResponsavel = Column(String, nullable=True)
    IdOrgaoResponsavel = Column(Integer, nullable=True)
    TemMultaCominatoria = Column(Boolean, default=False)
    NomeResponsavelMultaCominatoria = Column(String, nullable=True)
    DocumentoResponsavelMultaCominatoria = Column(String, nullable=True)
    IdPessoaMultaCominatoria = Column(Integer, nullable=True)
    ValorMultaCominatoria = Column(Float, nullable=True)
    PeriodoMultaCominatoria = Column(String, nullable=True)
    EMultaCominatoriaSolidaria = Column(Boolean, default=False)
    SolidariosMultaCominatoria = Column(JSONEncodedDict, nullable=True) # Usando o tipo JSON personalizado

# Cria as tabelas no banco de dados
Base.metadata.create_all(engine)

# Cria uma sessão de banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Função para obter a sessão do banco de dados ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()