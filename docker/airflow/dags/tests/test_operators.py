import os
import pytest
import PyPDF2
import pymssql

from langchain_openai import ChatOpenAI

from sqlalchemy import select
from sqlalchemy import create_engine, MetaData

from sqlalchemy.orm import Session

from dotenv import load_dotenv

from ..custom.models import Decisao, Obrigacao
from ..custom.llm_utils import classificar_determinacao_outro, classificar_itens_decisao, ObrigacaoPydantic

from ..custom.hooks import DecisaoHook
from ..custom.operators import DecisaoOperator

from dotenv import load_dotenv

metadata = MetaData()

def create_engine_db(db_name):
    load_dotenv('.env')

    db_user = os.getenv('SQLSERVER_USER')
    db_pass = os.getenv('SQLSERVER_PASS')
    db_host = os.getenv('SQLSERVER_HOST')
    db_port = os.getenv('SQLSERVER_PORT')

    pymssql.connect(server=db_host, user=db_user, password=db_pass, port=db_port)

    sql_str = "mssql+pymssql://%s:%s@%s:%s/%s" % (db_user, db_pass, db_host, db_port, db_name)
    return create_engine(sql_str)

@pytest.fixture
def llm():
    load_dotenv('.env')
    return ChatOpenAI(temperature=0, model_name='gpt-4o')

@pytest.mark.skip
def test_decisao(llm):
    with Session(create_engine_db(db_name='BdDIP')) as session:
        result = session.execute(select(Decisao).where(Decisao.c.ano_processo == '2024'))
        decisao = result.fetchone()
        assert decisao is not None

        reader = PyPDF2.PdfReader('relatorio_teste.pdf')
        text = ''

        for page in reader.pages:
            text += page.extract_text()

        is_decisao = classificar_determinacao_outro(text, llm) == 'DETERMINACAO'

        if is_decisao:
            r = classificar_itens_decisao(text, llm)

        determinacoes = r.determinacoes
        obrigacoes = []

        for determinacao in determinacoes:
            if type(determinacao) == ObrigacaoPydantic:
                obrigacoes.append(determinacao)

        for obrigacao in obrigacoes:
            o = Obrigacao(IdDecisao=decisao.IdInformacao, 
                        Prazo=obrigacao.prazo_obrigacao, 
                        Descricao=obrigacao.descricao, 
                        OrgaoResponsavel=obrigacao.orgao_responsavel)
            session.add(o)
        
        session.commit()


    classificar_determinacao_outro

@pytest.fixture
def informacoes_dir():
    return "/mnt/informacoes_pdf/"

@pytest.fixture
def openai_key():
    load_dotenv('.env')
    return os.getenv('OPENAI_API_KEY')

@pytest.fixture
def sql_connection():
    load_dotenv('.env')
    db_user = os.getenv('SQLSERVER_USER')
    db_pass = os.getenv('SQLSERVER_PASS')
    db_host = os.getenv('SQLSERVER_HOST')
    db_port = os.getenv('SQLSERVER_PORT')

    return pymssql.connect(server=db_host, user=db_user, password=db_pass, port=db_port)

def test_operator(mocker, informacoes_dir, openai_key, sql_connection):
    os.chdir('/home/eduardo/Dev/dip-blue/docker/airflow/dags/')
    mocker.patch.object(DecisaoOperator, 'get_informacoes_dir', return_value=informacoes_dir)
    mocker.patch.object(DecisaoOperator, 'get_openai_key', return_value=openai_key)
    mocker.patch.object(DecisaoHook, 'get_conn_dip', return_value=sql_connection)

    operator = DecisaoOperator(task_id="decisao_operator")

    r = operator.execute('2024-01-01', '2024-02-01', None)

    assert r is None

    