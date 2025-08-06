import pandas as pd

from langchain_openai import  AzureChatOpenAI, ChatOpenAI
from dotenv import load_dotenv

from tools.schema import Obrigacao, NERDecisao
from tools.models import ObrigacaoORM

from tools.prompt import generate_few_shot_ner_prompts

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

def get_chat_model():
    return AzureChatOpenAI(
    deployment_name="gpt-4-turbo",
    model_name="gpt-4")

extractor_obrigacao = get_chat_model().with_structured_output(Obrigacao, include_raw=False, method="json_schema")
extractor_decisao = get_chat_model().with_structured_output(NERDecisao, include_raw=False, method="json_schema")

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

def get_prompt_obrigacao(contexto, obrigacao):
    data_sessao = contexto['data_sessao']
    texto_acordao = contexto['texto_acordao']
    orgao_responsavel = contexto['orgao_responsavel']
    pessoas_responsaveis = contexto['responsaveis']


    return f"""
    Você é um Auditor de Controle Externo do TCE/RN. Sua tarefa é analisar o voto e extrair a obrigação imposta, preenchendo os campos do objeto Obrigacao.

    Data da Sessão: {data_sessao.strftime('%d/%m/%Y')}
    Obrigação detectada: {obrigacao.descricao_obrigacao}
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

def get_prompt_recomendacao(contexto, recomendacao):
    data_sessao = contexto['data_sessao']
    texto_acordao = contexto['texto_acordao']
    orgao_responsavel = contexto['orgao_responsavel']
    pessoas_responsaveis = contexto['responsaveis']

    return f"""
    Você é um Auditor de Controle Externo do TCE/RN. Sua tarefa é analisar o voto e extrair a recomendação proferida, preenchendo os campos do objeto Recomendacao.

    Data da Sessão: {data_sessao.strftime('%d/%m/%Y')}
    Recomendação detectada: {recomendacao.descricao_recomendacao}
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

def extract_obrigacao(row, obrigacao):
    prompt_obrigacao = get_prompt_obrigacao(row, obrigacao)
    return extractor_obrigacao.invoke(prompt_obrigacao)

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