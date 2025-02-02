from sqlalchemy import create_engine

from models import BaseDip
from db import engine_dip

def create_tables_bip():
    BaseDip.metadata.create_all(engine_dip)

if __name__ == "__main__":
    create_tables_bip()
