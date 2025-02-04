import datetime

from airflow.hooks.base import BaseHook

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sqlalchemy import select

from .models import Decisao, Obrigacao

class DecisaoHook(BaseHook):
    def __init__(self):
        super().__init__()
        self.conn_dip = self.get_conn_dip()

    def get_conn_dip(self):
        conn = self.get_connection('sqlserver_dip')
        return conn
    
    def get_engine_dip(self):
        sql_str = "mssql+pymssql://%s:%s@%s:%s/%s" % (self.conn_dip.login,  self.conn_dip.password, self.conn_dip.host, self.conn_dip.port, 'BdDIP')
        return create_engine(sql_str)
    
    def get_engine_processo(self):
        sql_str = "mssql+pymssql://%s:%s@%s:%s/%s" % (self.conn_dip.login,  self.conn_dip.password, self.conn_dip.host, self.conn_dip.port, 'processo')
        return create_engine(sql_str)

    def get_decisoes(self, data_inicio: datetime.datetime, data_fim: datetime.datetime):
        with Session(self.get_engine_dip()) as session:
            result = session.execute(select(Decisao).where(Decisao.c.DataPublicacao >= data_inicio).where(Decisao.c.DataPublicacao <= data_fim))
            return result.fetchall()
        
    def save_obrigacao(self, obrigacao: Obrigacao):
        sql_str = "mssql+pymssql://%s:%s@%s:%s/%s" % (self.conn_dip.login,  self.conn_dip.password, self.conn_dip.host, self.conn_dip.port, 'BdDIP')
        engine = create_engine(sql_str)

        with Session(engine) as session:
            o = Obrigacao(IdDecisao=obrigacao.IdInformacao, 
                        Prazo=obrigacao.prazo_obrigacao, 
                        Descricao=obrigacao.descricao, 
                        OrgaoResponsavel=obrigacao.orgao_responsavel)
            session.add(o)
            session.commit()