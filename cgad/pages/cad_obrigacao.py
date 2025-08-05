import os
import datetime
import json
import streamlit as st

from tools.models import ObrigacaoORM, ProcessoORM, DecisaoORM, get_db_dip, get_db_processo
from utils import extract_decisao_ner
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Cadastro de Obrigação", layout="centered")

st.title("Sistema de Cadastro de Obrigação")

st.markdown(
"""
Este formulário permite inserir novas obrigações no banco de dados.
Preencha os campos abaixo e clique em "Salvar Obrigação".
"""
)

def buscar_decisões():
    numero_processo = st.session_state.get("numero_processo_input")
    ano_processo = st.session_state.get("ano_processo_input")

    if not numero_processo or not ano_processo:
        st.error("Por favor, preencha o número e o ano do processo.")
        st.session_state.decisoes_encontradas = None
        return

    try:
        db_processo = next(get_db_processo())
        decisoes = db_processo.query(DecisaoORM).filter(
            DecisaoORM.NumeroProcesso == numero_processo,
            DecisaoORM.AnoProcesso == ano_processo
        ).all()
        if decisoes:
            st.session_state.decisoes_encontradas = decisoes
            if len(decisoes) == 1:
                st.success(f"Foi encontrada {len(decisoes)} decisão para o processo informado.")
            else:
                st.success(f"Foram encontradas {len(decisoes)} decisões para o processo informado.")
        else:
            st.warning("Decisões não encontradas.")
            st.session_state.decisoes_encontradas = None
    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar o processo: {e}")
        st.session_state.decisoes_encontradas = None
    finally:
        db_processo.close()

def extrair_itens(acordao):
    result = extract_decisao_ner(acordao)
    if result:
        st.session_state.decisao_extraida = result
        st.success("Decisão extraída com sucesso!")
    else:
        st.error("Não foi possível extrair a decisão do acórdão.")

col1_busca, col2_busca, col_btn_busca = st.columns([1, 1, 0.5])
with col1_busca:
    st.text_input("Número do Processo", key="numero_processo_input")
with col2_busca:
    st.text_input("Ano do Processo", key="ano_processo_input")
with col_btn_busca:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Buscar decisões", on_click=buscar_decisões)

if st.session_state.get("processo_encontrado"):
    st.info(f"Assunto do processo encontrado: **{st.session_state.processo_encontrado.assunto}**")

# Bloco para exibir os resultados da busca
if st.session_state.get("decisoes_encontradas"):
    st.subheader("Decisões encontradas")
    for p in st.session_state.decisoes_encontradas:
        acordao = getattr(p, "texto_acordao", None)
        st.text_area(label="Texto do Acórdão", value=acordao, height=300, disabled=True)
        st.button("Extrair itens da decisão", on_click=extrair_itens, args=(acordao,))

if st.session_state.get("decisao_extraida"):
    st.subheader("Decisão Extraída")
    for p in st.session_state.decisao_extraida:
        st.json(p)
            

with st.form("obrigacao_form", clear_on_submit=True):
    st.subheader("Obrigações")
    col3, col4 = st.columns(2)
    with col3:
        id_composicao_pauta = st.number_input("ID da Composição da Pauta", min_value=1, step=1, value=1)
        id_voto_pauta = st.number_input("ID do Voto da Pauta", min_value=1, step=1, value=1)
    with col4:
        descricao_obrigacao = st.text_area("Descrição da Obrigação", height=100)
        de_fazer = st.checkbox("É Obrigação de Fazer?", value=True)
        prazo = st.text_input("Prazo (ex: '30 dias', 'imediatamente')", value="")
        data_cumprimento = st.date_input("Data de Cumprimento", value=None, format="DD/MM/YYYY")

    st.subheader("Responsável e Multa Cominatória")
    col5, col6 = st.columns(2)
    with col5:
        orgao_responsavel = st.text_input("Órgão Responsável", value="")
        id_orgao_responsavel = st.number_input("ID do Órgão Responsável", min_value=0, step=1, value=0)
    with col6:
        tem_multa_cominatoria = st.checkbox("Tem Multa Cominatória?", value=False)

    # Novo botão para salvar a obrigação, que submete o formulário
    submitted = st.form_submit_button("Salvar Obrigação")

    if tem_multa_cominatoria:
        col7, col8 = st.columns(2)
        with col7:
            nome_responsavel_multa = st.text_input("Nome do Responsável pela Multa", value="")
            documento_responsavel_multa = st.text_input("Documento do Responsável pela Multa", value="")
            id_pessoa_multa = st.number_input("ID da Pessoa da Multa", min_value=0, step=1, value=0)
        with col8:
            valor_multa = st.number_input("Valor da Multa Cominatória", min_value=0.0, step=0.01, value=0.0)
            periodo_multa = st.text_input("Período da Multa (ex: 'diário', 'mensal')", value="")
            e_multa_solidaria = st.checkbox("É Multa Cominatória Solidária?", value=False)

        solidarios_multa = {}
        if e_multa_solidaria:
            st.markdown("---")
            st.write("Insira os Solidários da Multa (formato JSON, ex: `{\"nome\": \"João\", \"doc\": \"123\"}`)")
            solidarios_multa_input = st.text_area("Solidários da Multa Cominatória (JSON)", height=100, value="")
            try:
                if solidarios_multa_input:
                    solidarios_multa = json.loads(solidarios_multa_input)
            except json.JSONDecodeError:
                st.error("Formato JSON inválido para 'Solidários da Multa Cominatória'.")
                solidarios_multa = None

    if submitted:
        if not descricao_obrigacao:
            st.error("A 'Descrição da Obrigação' é um campo obrigatório.")
        elif not st.session_state.get("processo_encontrado"):
            st.error("Por favor, busque e encontre um processo antes de salvar a obrigação.")
        else:
            try:
                db_dip = next(get_db_dip())
                
                processo_id = st.session_state.processo_encontrado.IdProcesso

                new_obrigacao = ObrigacaoORM(
                    IdProcesso=processo_id,
                    IdComposicaoPauta=id_composicao_pauta,
                    IdVotoPauta=id_voto_pauta,
                    DescricaoObrigacao=descricao_obrigacao,
                    DeFazer=de_fazer,
                    Prazo=prazo if prazo else None,
                    DataCumprimento=data_cumprimento if data_cumprimento else None,
                    OrgaoResponsavel=orgao_responsavel if orgao_responsavel else None,
                    IdOrgaoResponsavel=id_orgao_responsavel if id_orgao_responsavel > 0 else None,
                    TemMultaCominatoria=tem_multa_cominatoria,
                )

                if tem_multa_cominatoria:
                    new_obrigacao.NomeResponsavelMultaCominatoria = nome_responsavel_multa if nome_responsavel_multa else None
                    new_obrigacao.DocumentoResponsavelMultaCominatoria = documento_responsavel_multa if documento_responsavel_multa else None
                    new_obrigacao.IdPessoaMultaCominatoria = id_pessoa_multa if id_pessoa_multa > 0 else None
                    new_obrigacao.ValorMultaCominatoria = valor_multa if valor_multa > 0 else None
                    new_obrigacao.PeriodoMultaCominatoria = periodo_multa if periodo_multa else None
                    new_obrigacao.EMultaCominatoriaSolidaria = e_multa_solidaria
                    new_obrigacao.SolidariosMultaCominatoria = solidarios_multa

                db_dip.add(new_obrigacao)
                db_dip.commit()
                db_dip.refresh(new_obrigacao)

                # Atualiza a lista de obrigações salvas na sessão
                if "obrigacoes_salvas" not in st.session_state:
                    st.session_state.obrigacoes_salvas = []
                st.session_state.obrigacoes_salvas.append(new_obrigacao)

                st.success(f"Obrigação com ID {new_obrigacao.IdObrigacao} salva com sucesso!")

            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar a obrigação: {e}")
                st.exception(e)
            finally:
                db_dip.close()

st.markdown("---")
st.subheader("Obrigações salvas nessa sessão")

db_session_display = next(get_db_dip())
obrigacoes = st.session_state.get("obrigacoes_salvas", [])

if obrigacoes:
    st.write(f"Total de obrigações: {len(obrigacoes)}")
    for ob in obrigacoes:
        st.json({
            "IdObrigacao": ob.IdObrigacao,
            "IdProcesso": ob.IdProcesso,
            "DescricaoObrigacao": ob.DescricaoObrigacao,
            "DeFazer": ob.DeFazer,
            "DataCumprimento": str(ob.DataCumprimento) if ob.DataCumprimento else None,
            "TemMultaCominatoria": ob.TemMultaCominatoria,
            "ValorMultaCominatoria": ob.ValorMultaCominatoria,
            "SolidariosMultaCominatoria": ob.SolidariosMultaCominatoria
        })
else:
    st.info("Nenhuma obrigação salva ainda.")