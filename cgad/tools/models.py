import os
import json

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, Date, DateTime, Numeric, ForeignKey, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator, TEXT
from dotenv import load_dotenv

load_dotenv() 

DATABASE_URL_DIP = f"mssql+pymssql://{os.getenv('SQL_SERVER_USER')}:{os.getenv('SQL_SERVER_PASS')}@{os.getenv('SQL_SERVER_HOST')}/{os.getenv('SQL_SERVER_DB')}"
DATABASE_URL_PROCESSO = f"mssql+pymssql://{os.getenv('SQL_SERVER_USER')}:{os.getenv('SQL_SERVER_PASS')}@{os.getenv('SQL_SERVER_HOST')}/processo"

engine_dip = create_engine(DATABASE_URL_DIP, 
                            pool_pre_ping=True,
                            pool_recycle=3600)
engine_processo = create_engine(DATABASE_URL_PROCESSO, 
                            pool_pre_ping=True,
                            pool_recycle=3600)

BaseDIP = declarative_base()
BaseProcesso = declarative_base()

class JSONEncodedDict(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value



class ProcessoORM(BaseProcesso):
    __tablename__ = 'Processos'
    __table_args__ = {'schema': 'dbo'}

    IdProcesso = Column(Integer, primary_key=True, autoincrement=True)
    numero_processo = Column(String(255), nullable=False)
    ano_processo = Column(String(4), nullable=False)
    codigo_camara = Column(String(1), nullable=False)
    data_registro = Column(DateTime, nullable=False)
    codigo_tipo_processo = Column(String(3), ForeignKey('dbo.Tipo.codigo'), nullable=False)
    assunto = Column(String(255))
    interessado = Column(String(255))
    numero_origem = Column(String(30), nullable=False)
    ano_origem = Column(String(4), nullable=False)
    idprocessoorigemexecucao = Column(Integer)
    sigla_origem = Column(String(10), nullable=False)
    valor = Column(Numeric(19, 4))
    apensador = Column(Boolean)
    codigo_relator = Column(String(2), ForeignKey('dbo.Relator.codigo'))
    ano_referencia = Column(String(4))
    mes_referencia = Column(String(2))
    setor_atual = Column(String(10))
    natureza = Column(String(1), nullable=False)
    numero_apensador = Column(String(255))
    ano_apensador = Column(String(4))
    em_diligencia = Column(String(1))
    data_ultima_atualizacao = Column(DateTime)
    usuario = Column(String(11))
    DataInclusao = Column(DateTime)
    TipoSorteio = Column(String(2))
    TipoSorteioProcurador = Column(String(2))
    codigo_procurador = Column(String(2))
    data_atribuicao = Column(DateTime)
    UsuarioSorteio = Column(String(11))
    ValorDoProcesso = Column(Numeric(19, 4))
    ObjetoDoProcesso = Column(String(2000))
    CodigoModalidade = Column(String(4))
    IdTipoFaseProcessualAtual = Column(Integer)
    IdSessao = Column(Integer)
    Sigilo = Column(Boolean)
    CaraterSeletivo = Column(Boolean)
    Digitalizacao = Column(String(1))
    DataDigitalizacao = Column(DateTime)
    usuarioDigitalizacao = Column(String(11))
    SetorDigitalizacao = Column(String(10))
    ProcessoDigitalizado = Column(String(1))
    ProcessoaDigitalizar = Column(String(1))
    transitoemjulgado = Column(String(1))
    IdOrgaoEnvolvido = Column(Integer)
    RespostaComunicacao = Column(String(20))
    numero_sessao_processo = Column(String(5))
    ano_sessao_processo = Column(String(4))
    ApensamentoVolumes = Column(SmallInteger)
    ApensamentoPagina = Column(SmallInteger)
    DigitalizadoNoOrgao = Column(String(1))
    ProcessoemRestauracao = Column(Boolean)
    ObservacaoDIN = Column(String(500))
    IdProcessoApensador = Column(Integer)
    TipoDiligencia = Column(String(1))
    DataUltimoRecebimento = Column(DateTime)
    TramitacaoAberta = Column(Boolean)
    IdModalidade = Column(SmallInteger, ForeignKey('dbo.Pro_Modalidade.IdModalidade'))
    UsuarioProtocoloEletronico = Column(String(11))
    TipoSustentacaoOral = Column(String(1))

    #relator = relationship("Relator", backref="processos")
    #tipo = relationship("Tipo", backref="processos")
    #modalidade = relationship("Pro_Modalidade", backref="processos")

    def __repr__(self):
        return f"<Processos(IdProcesso={self.IdProcesso}, numero_processo='{self.numero_processo}', ano_processo='{self.ano_processo}')>"
    
class DecisaoORM(BaseProcesso):
    __tablename__ = 'vw_ia_votos_acordaos_decisoes'
    __table_args__ = {'schema': 'dbo'}

    idvoto = Column(Integer, primary_key=True)
    codigo_tipo_processo = Column(String(255))
    descricao = Column(String(255))
    TipoVoto = Column(String(255))
    VotoEscolhido = Column(Integer)
    IdInformacao_Voto = Column(Integer)
    INFO_arquivo_Voto = Column(String(255))
    IdComposicaoPauta = Column(Integer)
    CodigoCamara = Column(String(255))
    numero_sessao = Column(String(255))
    ano_sessao = Column(String(255))
    DataSessao = Column(DateTime)
    DataEncerramentoSessao = Column(DateTime)
    numeroResultado = Column(Integer)
    anoResultado = Column(String(255))
    resultadoTipo = Column(String(255))
    IdApreciacao = Column(Integer)
    idTipoRecurso = Column(Integer)
    idTipoVotacao = Column(Integer)
    decisao = Column(String(255))
    idVotoPauta = Column(Integer)
    idVotoDecisao = Column(Integer)
    NomeRelator = Column(String(255))
    Setor = Column(String(255))
    ementa = Column(Text)
    assunto = Column(String(255))
    NumeroProcesso = Column(String(255))
    AnoProcesso = Column(String(255))
    NomeRelatorProcesso = Column(String(255))
    IdProcesso = Column(Integer)
    interessado = Column(String(255))
    OrgaoOrigem = Column(String(255))
    Divergente_de_idVoto = Column(Integer)
    isVotoDivergente = Column(Boolean)
    IdVotoConcordado = Column(Integer)
    Relatorio = Column(String(255))
    FundamentacaoVoto = Column(String(255))
    Conclusao = Column(String(255))
    Artigo = Column(String(255))
    texto_acordao = Column(Text)
    SetorVoto = Column(String(255))
    DescricaoTipoVoto = Column(String(255))

class ObrigacaoORM(BaseDIP):
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
    SolidariosMultaCominatoria = Column(JSONEncodedDict, nullable=True)
    Cancelado = Column(Boolean, default=False)

class RecomendacaoORM(BaseDIP):
    __tablename__ = "Recomendacao"

    IdRecomendacao = Column(Integer, primary_key=True, index=True)
    IdProcesso = Column(Integer, nullable=False)
    IdComposicaoPauta = Column(Integer, nullable=False)
    IdVotoPauta = Column(Integer, nullable=False)
    DescricaoRecomendacao = Column(Text, nullable=True)
    PrazoCumprimentoRecomendacao = Column(String, nullable=True)
    DataCumprimentoRecomendacao = Column(Date, nullable=True)
    NomeResponsavel = Column(String, nullable=True)
    IdPessoaResponsavel = Column(Integer, nullable=True)
    OrgaoResponsavel = Column(String, nullable=True)
    IdOrgaoResponsavel = Column(Integer, nullable=True)
    Cancelado = Column(Boolean, nullable=True)

    def __repr__(self):
        return f"<Recomendacao(IdRecomendacao={self.IdRecomendacao}, descricao_recomendacao='{self.DescricaoRecomendacao[:30]}...',\
              NomeResponsavel='{self.NomeResponsavel}', DataCumprimentoRecomendacao='{self.DataCumprimentoRecomendacao}', IdOrgaoResponsavel='{self.IdOrgaoResponsavel}',\
                IdPessoaResponsavel='{self.IdPessoaResponsavel}', Cancelado='{self.Cancelado}')>"
    
class CancelamentoObrigacao(BaseDIP):
    __tablename__ = "CancelamentoObrigacao"
    IdCancelamentoObrigacao = Column(Integer, primary_key=True)
    IdObrigacao = Column(Integer, ForeignKey('Obrigacao.IdObrigacao'), nullable=False)
    MotivoCancelamento = Column(String)
    DataCancelamento = Column(Date, nullable=False, default="CURRENT_TIMESTAMP")
    
class CancelamentoRecomendacao(BaseDIP):
    __tablename__ = "CancelamentoRecomendacao"
    IdCancelamentoRecomendacao = Column(Integer, primary_key=True)
    IdRecomendacao = Column(Integer, ForeignKey('Recomendacao.IdRecomendacao'), nullable=False)
    MotivoCancelamento = Column(String)
    DataCancelamento = Column(Date, nullable=False, default="CURRENT_TIMESTAMP")
    
SessionLocal_DIP = sessionmaker(autocommit=False, autoflush=False, bind=engine_dip)
SessionLocal_Processo = sessionmaker(autocommit=False, autoflush=False, bind=engine_processo)

def get_db_dip():
    db = SessionLocal_DIP()
    try:
        yield db
    finally:
        db.close()
        
def get_db_processo():
    db = SessionLocal_Processo()
    try:
        yield db
    finally:
        db.close()