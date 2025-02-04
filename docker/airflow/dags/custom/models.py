from typing import List
from typing import Optional

from sqlalchemy import ForeignKey, String, Integer, Table, Text, Boolean, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship

BaseDip = declarative_base()

Decisao = Table("vwDecisao", BaseDip.metadata)

class Obrigacao(BaseDip):
    __tablename__ = "Obrigacao"
    IdObrigacao: Mapped[int] = Column(primary_key=True)
    IdDecisao: Mapped[int] = Column(Integer)
    Prazo: Mapped[str] = Column(Text)
    Descricao: Mapped[str] = Column(Text)
    OrgaoResponsavel: Mapped[str] = Column(Text)
    Processado: Mapped[Optional[bool]] = Column(Boolean)
    Validado: Mapped[Optional[bool]] = Column(Boolean)
    def __repr__(self) -> str:
        return f"Obrigacao (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    
class Monitoramento(BaseDip):
    __tablename__ = "Monitoramento"
    IdMonitoramento: Mapped[int] = Column(primary_key=True)
    IdDecisao: Mapped[int] = Column(Integer)
    DataMonitoramento: Mapped[str] = Column(String(10))
    Descricao: Mapped[str] = Column(Text)
    Irregularidades: Mapped[List[Optional["Irregularidade"]]] = relationship("Irregularidade")
    def __repr__(self) -> str:
        return f"Monitoramento (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    
class Irregularidade(BaseDip):
    __tablename__ = "Irregularidade"
    IdIrregularidade: Mapped[int] = Column(primary_key=True)
    IdMonitoramento: Mapped[int] = Column(ForeignKey("Monitoramento.IdMonitoramento"))
    Descricao: Mapped[str] = Column(Text)
    def __repr__(self) -> str:
        return f"Irregularidade (IdDecisao={self.IdDecisao!r}, Descricao={self.Descricao!r})"
    