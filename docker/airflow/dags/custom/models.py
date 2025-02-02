from typing import List
from typing import Optional

from sqlalchemy import ForeignKey, String, Integer, Table, Text, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from db import metadata, engine_dip, engine_processo, engine_bdc

class BaseDip(DeclarativeBase):
    pass

Processo = Table("Processos", metadata, autoload_with=engine_processo)
Decisao = Table("vwDecisao", BaseDip.metadata, autoload_with=engine_dip)
Debito = Table("Exe_Debito", metadata, autoload_with=engine_processo)
#Orgao = Table("Gen_Orgao", metadata, autoload_with=engine_processo)

class Obrigacao(BaseDip):
    __tablename__ = "Obrigacao"
    IdObrigacao: Mapped[int] = mapped_column(primary_key=True)
    IdDecisao: Mapped[int] = mapped_column(Integer)
    Prazo: Mapped[str] = mapped_column(Text)
    Descricao: Mapped[str] = mapped_column(Text)
    OrgaoResponsavel: Mapped[str] = mapped_column(Text)
    Processado: Mapped[Optional[bool]] = mapped_column(Boolean)
    Validado: Mapped[Optional[bool]] = mapped_column(Boolean)
    def __repr__(self) -> str:
        return f"Obrigacao (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    
class Monitoramento(BaseDip):
    __tablename__ = "Monitoramento"
    IdMonitoramento: Mapped[int] = mapped_column(primary_key=True)
    IdDecisao: Mapped[int] = mapped_column(Integer)
    DataMonitoramento: Mapped[str] = mapped_column(String(10))
    Descricao: Mapped[str] = mapped_column(Text)
    Irregularidades: Mapped[List[Optional["Irregularidade"]]] = relationship("Irregularidade")
    def __repr__(self) -> str:
        return f"Monitoramento (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    
class Irregularidade(BaseDip):
    __tablename__ = "Irregularidade"
    IdIrregularidade: Mapped[int] = mapped_column(primary_key=True)
    IdMonitoramento: Mapped[int] = mapped_column(ForeignKey("Monitoramento.IdMonitoramento"))
    Descricao: Mapped[str] = mapped_column(Text)
    def __repr__(self) -> str:
        return f"Irregularidade (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    