import pytest

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..custom.db import create_engine_db
from ..custom.models import Processo, Decisao

@pytest.mark.skip
def test_connection():
    engine = create_engine_db(db_name='BdDIP')
    connection = engine.connect()
    connection.close()
    engine.dispose()

@pytest.mark.skip
def test_decisao():
    with Session(create_engine_db(db_name='BdDIP')) as session:
        result = session.execute(select(Decisao).where(Decisao.c.ano_processo == '2024'))
        decisao = result.fetchone()
        assert decisao is not None
