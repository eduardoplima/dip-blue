import pytest

from ..custom.db import create_engine_db
from ..custom.models import Processos, Decisao

@pytest.mark.skip
def test_connection():
    engine = create_engine_db(db_name='BdDIP')
    connection = engine.connect()
    connection.close()
    engine.dispose()

def test_processos():
    processo = Processos.select().where(Processos.c.AnoProcesso == '2024').execute().fetchone()
    assert processo is not None

