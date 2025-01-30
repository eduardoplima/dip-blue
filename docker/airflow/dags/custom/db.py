import os 
import pymssql

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

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

engine_dip = create_engine_db('BdDIP')
engine_processo = create_engine_db('processo')
engine_bdc = create_engine_db('BdC')