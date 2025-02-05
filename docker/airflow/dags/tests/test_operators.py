import os
import pytest
import PyPDF2
import pymssql

from airflow.models import Connection

from langchain_openai import ChatOpenAI

from sqlalchemy import select
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from dotenv import load_dotenv

from ..custom.models import Obrigacao
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

    return Connection(host=db_host, login=db_user, password=db_pass, port=db_port)

def test_operator(mocker, informacoes_dir, openai_key, sql_connection):
    os.chdir('/home/eduardo/Dev/dip-blue/docker/airflow/dags/')
    mocker.patch.object(DecisaoOperator, 'get_informacoes_dir', return_value=informacoes_dir)
    mocker.patch.object(DecisaoOperator, 'get_openai_key', return_value=openai_key)
    mocker.patch.object(DecisaoHook, 'get_conn_dip', return_value=sql_connection)

    operator = DecisaoOperator(task_id="decisao_operator")

    r = operator.execute('2024-01-01', '2024-02-01', None)

    assert r is None

    