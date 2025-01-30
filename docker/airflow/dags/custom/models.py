from typing import List
from typing import Optional

from sqlalchemy import ForeignKey, String, Column, Integer, Table, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .db import metadata, engine_dip, engine_processo, engine_bdc

class Base(DeclarativeBase):
    pass

Processo = Table("Processos", metadata, autoload_with=engine_processo)
Debito = Table("Exe_debito", metadata, autoload_with=engine_processo)
Orgao = Table("Gen_Orgao", metadata, autoload_with=engine_bdc)

class Decisao(Base):
    __tablename__ = "Decisao"
    IdDecisao: Mapped[int] = mapped_column(primary_key=True)
    NumeroProcesso: Mapped[str] = mapped_column(String(6))
    AnoProcesso: Mapped[str] = mapped_column(String(4))
    DataDecisao: Mapped[str] = mapped_column(String(10))
    DescricaoDecisao: Mapped[str] = mapped_column(String(100))
    IdProcesso: Mapped[int] = mapped_column(ForeignKey("Processos.IdProcesso"))
    Evento: Mapped[int] = mapped_column(Integer)
    CaminhoArquivo: Mapped[str] = mapped_column(String(100))
    TextoArquivo: Mapped[str] = mapped_column(Text)
    def __repr__(self) -> str:
        return f"Decisao (NumeroProcesso={self.NumeroProcesso!r}, AnoProcesso={self.AnoProcesso!r}, DataDecisao={self.DataDecisao!r}, IdProcesso={self.IdProcesso!r})"

class Obrigacao(Base):
    __tablename__ = "Obrigacao"
    IdObrigacao: Mapped[int] = mapped_column(primary_key=True)
    IdDecisao: Mapped[int] = mapped_column(ForeignKey("Decisoes.IdDecisao"))
    DataVencimento: Mapped[str] = mapped_column(String(10))
    Descricao: Mapped[str] = mapped_column(Text)
    def __repr__(self) -> str:
        return f"Obrigacao (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    
class Monitoramento(Base):
    __tablename__ = "Monitoramento"
    IdMonitoramento: Mapped[int] = mapped_column(primary_key=True)
    IdDecisao: Mapped[int] = mapped_column(ForeignKey("Decisoes.IdDecisao"))
    DataMonitoramento: Mapped[str] = mapped_column(String(10))
    Descricao: Mapped[str] = mapped_column(Text)
    Irregularidades: Mapped[List[Optional["Irregularidade"]]] = relationship("Irregularidade")
    def __repr__(self) -> str:
        return f"Monitoramento (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    
class Irregularidade(Base):
    __tablename__ = "Irregularidade"
    IdIrregularidade: Mapped[int] = mapped_column(primary_key=True)
    IdMonitoramento: Mapped[int] = mapped_column(ForeignKey("Monitoramento.IdMonitoramento"))
    Descricao: Mapped[str] = mapped_column(Text)
    def __repr__(self) -> str:
        return f"Irregularidade (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    