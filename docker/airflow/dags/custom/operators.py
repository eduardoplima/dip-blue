import PyPDF2
import pathlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from airflow.models import BaseOperator, Variable
from airflow.utils.decorators import apply_defaults

from langchain_openai import ChatOpenAI

from .llm_utils import classificar_determinacao_outro, classificar_itens_decisao, ObrigacaoPydantic
from .models import Obrigacao, Table, BaseDip
from .hooks import DecisaoHook
  
class DecisaoOperator(BaseOperator):
    def __init__(self, *args, **kwargs):
        super(DecisaoOperator, self).__init__(*args, **kwargs)
        self.llm = self.get_llm()
        self.hook = DecisaoHook()

    def get_openai_key(self):
        return Variable.get("openai_key")
    
    def get_informacoes_dir(self):
        return Variable.get("informacoes_dir")
    
    def get_llm(self):
        return ChatOpenAI(temperature=0, model_name='gpt-4o', api_key=self.get_openai_key())

    def save_decisao(self, decisao):
        with Session(self.hook.get_engine_dip()) as session:
            llm = self.llm
            
            reader = PyPDF2.PdfFileReader(pathlib.Path(self.get_informacoes_dir()) / decisao.Arquivo)
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

    def execute(self, data_inicio, data_fim, context):
        decisoes = self.hook.get_decisoes(data_inicio, data_fim)

        for decisao in decisoes:
            llm = self.llm
            
            reader = PyPDF2.PdfReader(pathlib.Path(self.get_informacoes_dir()) / decisao.arquivo)
            text = ''
            for page in reader.pages:
                text += page.extract_text()

            is_decisao = classificar_determinacao_outro(text, llm) == 'DETERMINACAO'

            r = None
            if is_decisao:
                r = classificar_itens_decisao(text, llm)
            else:
                continue

            determinacoes = r.determinacoes
            obrigacoes = []

            for determinacao in determinacoes:
                if type(determinacao) == ObrigacaoPydantic:
                    obrigacoes.append(determinacao)

            for obrigacao in obrigacoes:
                self.hook.save_obrigacao(obrigacao)

        return super().execute(context)

    

        