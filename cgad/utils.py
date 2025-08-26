
import os
import pymssql
import datetime
import math

import pandas as pd

from datetime import date, datetime
from langchain_openai import  AzureChatOpenAI, ChatOpenAI

from tools.schema import Obrigacao, Recomendacao, NERDecisao
from tools.models import ObrigacaoORM
from tools.prompt import generate_few_shot_ner_prompts

from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

def get_chat_model():
    return AzureChatOpenAI(
    deployment_name="gpt-4-turbo",
    model_name="gpt-4")

extractor_obrigacao = get_chat_model().with_structured_output(Obrigacao, include_raw=False, method="json_schema")
extractor_decisao = get_chat_model().with_structured_output(NERDecisao, include_raw=False, method="json_schema")
extractor_recomendacao = get_chat_model().with_structured_output(Recomendacao, include_raw=False, method="json_schema")


def _unwrap(v):
    """Return a plain scalar from pandas/NumPy/list/tuple/df/series/etc."""
    if v is None:
        return None

    # pandas first
    try:
        import pandas as pd
        if isinstance(v, pd.DataFrame):
            return None if v.empty else v.iloc[0, 0]
        if isinstance(v, (pd.Series, pd.Index)):
            return None if len(v) == 0 else v.iloc[0]
        if v is pd.NaT:
            return None
    except Exception:
        pass

    # numpy next
    try:
        import numpy as np
        if isinstance(v, np.ndarray):
            return None if v.size == 0 else v.flat[0]
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, np.datetime64):
            # convert to python date
            return datetime.utcfromtimestamp(
                v.astype('datetime64[ns]').astype('int') / 1e9
            ).date()
    except Exception:
        pass

    # plain containers
    if isinstance(v, (list, tuple, set)):
        for item in v:
            return item  # first element
        return None

    return v

def to_bool(v, default=False):
    v = _unwrap(v)
    if v in (None, ''):
        return default
    if isinstance(v, bool):
        return v
    try:
        import numpy as np
        if isinstance(v, np.bool_):
            return bool(v)
    except Exception:
        pass
    if isinstance(v, (int, float)):
        try:
            if isinstance(v, float) and math.isnan(v):
                return default
        except Exception:
            pass
        return v != 0
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {'true','1','t','yes','y','sim','s','on'}:
            return True
        if s in {'false','0','f','no','n','nao','não','off'}:
            return False
    return bool(v)

def to_float(v, default=None):
    v = _unwrap(v)
    if v in (None, ''):
        return default
    try:
        if isinstance(v, float) and math.isnan(v):
            return default
    except Exception:
        pass
    try:
        if isinstance(v, str):
            s = v.strip().replace('R$', '').replace(' ', '')
            # handle "1.234,56" -> "1234.56"
            if ',' in s:
                s = s.replace('.', '').replace(',', '.')
            return float(s)
        return float(v)
    except (TypeError, ValueError):
        return default

def to_int(v, default=None):
    v = _unwrap(v)
    if v in (None, ''):
        return default
    try:
        # handle NaN
        if isinstance(v, float) and math.isnan(v):
            return default
    except Exception:
        pass
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def to_pos_int_or_none(v):
    n = to_int(v, default=None)
    return n if (n is not None and n > 0) else None


def to_str_or_none(v):
    v = _unwrap(v)
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def to_date_or_none(v):
    v = _unwrap(v)
    if v is None:
        return None

    # pandas Timestamp?
    try:
        import pandas as pd
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime().date()
        # try generic parsing if it's a string or similar
        parsed = pd.to_datetime(v, dayfirst=True, errors="coerce")
        if not pd.isna(parsed):
            return parsed.to_pydatetime().date()
    except Exception:
        pass

    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        # best-effort ISO / common formats
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                continue
    return None


def safe_int(value):
    if pd.isna(value):
        return None
    return int(value)


def find_obrigacao_by_descricao(df_ob, descricao):
    return [i for i,r in df_ob.iterrows() if descricao in r['obrigacoes'][0].descricao_obrigacao][0]

def get_id_pessoa_multa_cominatoria(row, result_obrigacao):
    """
    Obtém o ID da pessoa responsável pela multa cominatória.
    """
    if result_obrigacao.documento_responsavel_multa_cominatoria:
        return [p['id_pessoa'] for p in row['responsaveis'] if p['documento_responsavel'] == result_obrigacao.documento_responsavel_multa_cominatoria][0]
    return None

def get_pessoas_str(pessoas):    
    pessoas_str = []
    for pessoa in pessoas:
        nome = pessoa.get('nome_responsavel', 'Desconhecido')
        documento = pessoa.get('documento_responsavel', 'Desconhecido')
        tipo = pessoa.get('tipo_responsavel', 'Desconhecido')
        if tipo == 'F':
            tipo = 'Física'
        elif tipo == 'J':
            tipo = 'Jurídica'
        pessoas_str.append(f"{nome} ({tipo} - {documento})")
    
    return ", ".join(pessoas_str)

def get_connection():
    """Establish a connection to the SQL Server database.
    Returns:
        pymssql.Connection: A connection object to the SQL Server database.
    """
    return pymssql.connect(
        server=os.getenv('SQL_SERVER_HOST'),
        user=os.getenv('SQL_SERVER_USER'),
        password=os.getenv('SQL_SERVER_PASS'),
        database='processo'
    )

def get_orgaos():
    query = f"""
    SELECT IdOrgao as id, Nome as nome
    FROM processo.dbo.Orgaos
    """
    df_orgaos = pd.read_sql(query, get_connection())
    if df_orgaos.empty:
        return None
    else:
        df_orgaos['nome'] = df_orgaos['nome'].str.strip()
        df_orgaos['nome'] = df_orgaos['nome'].str.upper()
        return df_orgaos

def get_pessoas():
    query = f"""
    SELECT DISTINCT gp.IdPessoa as id, gp.Nome as nome
    FROM processo.dbo.Pro_ProcessosResponsavelDespesa pprd INNER JOIN
    processo.dbo.GenPessoa gp ON pprd.IdPessoa = gp.IdPessoa 
    """
    df_pessoas = pd.read_sql(query, get_connection())
    if df_pessoas.empty:
        return None
    else:
        df_pessoas['nome'] = df_pessoas['nome'].str.strip()
        df_pessoas['nome'] = df_pessoas['nome'].str.upper()
        return df_pessoas

def get_df_decisao(numero_processo, ano_processo):
    query = f"""
    SELECT p.idprocesso as id_processo, 
    NumeroProcesso as numero_processo, 
    AnoProcesso as ano_processo, 
    IdComposicaoPauta as id_composicao_pauta, 
    idVotoPauta as id_voto_pauta,
    p.Assunto as assunto, 
    numero_sessao, 
    ano_sessao, 
    DataSessao as data_sessao,  
    Relatorio as relatorio, 
    FundamentacaoVoto as fundamentacao_voto, 
    Conclusao as conclusao, 
    texto_acordao, 
    o.nome as orgao_responsavel, 
    o.IdOrgao as id_orgao_responsavel,
    gp.Nome as nome_responsavel, 
    gp.Documento as documento_responsavel, 
    gp.TipoPessoa as tipo_responsavel, 
    gp.idpessoa as id_pessoa
    FROM processo.dbo.vw_ia_votos_acordaos_decisoes ia 
    LEFT JOIN processo.dbo.processos p ON ia.NumeroProcesso = p.numero_processo  AND ia.AnoProcesso = p.ano_processo 
    LEFT JOIN processo.dbo.Orgaos o ON o.IdOrgao = p.IdOrgaoEnvolvido
    LEFT JOIN processo.dbo.Pro_ProcessosResponsavelDespesa pprd ON p.IdProcesso = pprd.IdProcesso 
    LEFT JOIN processo.dbo.GenPessoa gp ON pprd.IdPessoa = gp.IdPessoa 
    WHERE p.numero_processo = {numero_processo}
    AND p.ano_processo = {ano_processo}
    """

    df = pd.read_sql(query, get_connection())

    if df.empty:
        return df

    group_cols = [
            'id_processo', 'numero_processo', 'ano_processo', 'id_composicao_pauta', 'assunto', 
            'id_voto_pauta', 'numero_sessao', 'ano_sessao', 'data_sessao', 'relatorio',
            'fundamentacao_voto', 'conclusao', 'texto_acordao', 'orgao_responsavel', 'id_orgao_responsavel',
    ]

    # Define as colunas para criar o dicionário de pessoas
    person_cols = ['nome_responsavel', 'documento_responsavel', 'tipo_responsavel', 'id_pessoa']

    # Agrupa o DataFrame e aplica uma função lambda para criar a lista de dicionários
    
    df = df.groupby(group_cols, dropna=False).apply(
        lambda x: pd.Series({'responsaveis': x[person_cols].apply(
            lambda y: y.dropna().to_dict(), axis=1
        ).tolist()})
    ).reset_index()

    df['data_sessao'] = pd.to_datetime(df['data_sessao'], errors='coerce')
    return df

def get_prompt_obrigacao(contexto, descricao_obrigacao):
    data_sessao = pd.to_datetime(contexto['data_sessao']).iloc[0]
    data_sessao = data_sessao.strftime('%d/%m/%Y')
    texto_acordao = contexto['texto_acordao'].values[0]
    orgao_responsavel = contexto['orgao_responsavel'].values[0]
    pessoas_responsaveis = contexto['responsaveis'].values[0]


    return f"""
    Você é um Auditor de Controle Externo do TCE/RN. Sua tarefa é analisar o voto e extrair a obrigação imposta, preenchendo os campos do objeto Obrigacao.

    Data da Sessão: {data_sessao}
    Obrigação detectada: {descricao_obrigacao}
    Texto do Acordão: {texto_acordao}
    Órgão Responsável: {orgao_responsavel}
    Pessoas Responsáveis: {get_pessoas_str(pessoas_responsaveis)}

    Dado esse contexto, preencha os campos da seguinte forma:
    - descricao_obrigacao: Descrição da obrigação imposta.
    - tipo: Tipo da obrigação (fazer/não fazer).
    - prazo: Prazo estipulado para cumprimento. Extraia o texto indicando o prazo, se houver. Exemplo: "90 dias".
    - data_cumprimento: Extraia do prazo do acórdão como data de início e faça o cálculo da data de cumprimento. Exemplo: 2025-09-13
    - orgao_responsavel: Órgão responsável pelo cumprimento da obrigação. Pessoa jurídica.
    - tem_multa_cominatoria: Indique se há multa cominatória associada à obrigação.
    - nome_responsavel_multa_cominatoria: Nome do responsável pela obrigação, se houver multa cominatória. Pessoa física responsável.
    - documento_responsavel_multa_cominatoria: Documento do responsável pela obrigação, se houver multa cominatória.
    - valor_multa_cominatoria: Se houver multa cominatória, preencha o valor.
    - periodo_multa_cominatoria: Período da multa cominatória, se houver.
    - e_multa_cominatoria_solidaria: Indique se a multa cominatória é solidária.
    - solidarios_multa_cominatoria: Lista de responsáveis solidários da multa cominatória.

    Use somente as informações do texto do acórdão e dos dados fornecidos. Não inclua informações adicionais ou suposições.
    Se o órgão responsável não estiver disponível, preencha o campo orgão_responsavel com "Desconhecido".
    """

from datetime import date

def get_prompt_recomendacao(contexto, descricao_recomendacao):
    data_sessao = pd.to_datetime(contexto['data_sessao']).iloc[0]
    data_sessao = data_sessao.strftime('%d/%m/%Y')
    texto_acordao = contexto['texto_acordao'].values[0]
    orgao_responsavel = contexto['orgao_responsavel'].values[0]
    pessoas_responsaveis = contexto['responsaveis'].values[0]

    return f"""
    Você é um Auditor de Controle Externo do TCE/RN. Sua tarefa é analisar o voto e extrair a recomendação proferida, preenchendo os campos do objeto Recomendacao.

    Data da Sessão: {data_sessao}
    Recomendação detectada: {descricao_recomendacao}
    Texto do Acordão: {texto_acordao}
    Órgão Responsável: {orgao_responsavel}
    Pessoas Responsáveis: {get_pessoas_str(pessoas_responsaveis)}

    Dado esse contexto, preencha os campos da seguinte forma:
    - descricao_recomendacao: Descrição da recomendação proferida.
    - prazo_cumprimento_recomendacao: Prazo sugerido para adoção da recomendação. Extraia o texto indicando o prazo, se houver. Exemplo: "90 dias".
    - data_cumprimento_recomendacao: Extraia do prazo do acórdão como data de início e faça o cálculo da data de cumprimento. Exemplo: 2025-09-13
    - nome_responsavel_recomendacao: Nome do responsável pela recomendação. Pessoa física.
    - orgao_responsavel_recomendacao: Órgão responsável pela recomendação. Pessoa jurídica.

    Use somente as informações do texto do acórdão e dos dados fornecidos. Não inclua informações adicionais ou suposições.
    Se o órgão responsável não estiver disponível, preencha o campo orgao_responsavel_recomendacao com "Desconhecido".
    """

def extract_obrigacao(contexto, descricao_obrigacao):
    prompt_obrigacao = get_prompt_obrigacao(contexto, descricao_obrigacao)
    return extractor_obrigacao.invoke(prompt_obrigacao)

def extract_recomendacao(contexto, descricao_recomendacao):
    prompt_recomendacao = get_prompt_recomendacao(contexto, descricao_recomendacao)
    return extractor_recomendacao.invoke(prompt_recomendacao)

def extract_decisao_ner(acordao):
    prompt_decisao = generate_few_shot_ner_prompts(acordao)
    return extractor_decisao.invoke(prompt_decisao)

def insert_obrigacao(db_session, obrigacao: Obrigacao, row):
    orm_obj = ObrigacaoORM(
        IdProcesso=safe_int(row['id_processo']),
        IdComposicaoPauta=safe_int(row['id_composicao_pauta']),
        IdVotoPauta=safe_int(row['id_voto_pauta']),
        DescricaoObrigacao=obrigacao.descricao_obrigacao,
        DeFazer=obrigacao.de_fazer,
        Prazo=obrigacao.prazo,
        DataCumprimento=obrigacao.data_cumprimento,
        OrgaoResponsavel=obrigacao.orgao_responsavel,
        IdOrgaoResponsavel=safe_int(row['id_orgao_responsavel']),
        TemMultaCominatoria=obrigacao.tem_multa_cominatoria,
        NomeResponsavelMultaCominatoria=obrigacao.nome_responsavel_multa_cominatoria,
        DocumentoResponsavelMultaCominatoria=obrigacao.documento_responsavel_multa_cominatoria,
        IdPessoaMultaCominatoria=get_id_pessoa_multa_cominatoria(row, obrigacao),
        ValorMultaCominatoria=obrigacao.valor_multa_cominatoria,
        PeriodoMultaCominatoria=obrigacao.periodo_multa_cominatoria,
        EMultaCominatoriaSolidaria=obrigacao.e_multa_cominatoria_solidaria,
        SolidariosMultaCominatoria=obrigacao.solidarios_multa_cominatoria
    )
    db_session.add(orm_obj)
    db_session.commit()
    return orm_obj