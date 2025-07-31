import os
import datetime
import json

import streamlit as st

from models import ObrigacaoORM, get_db
from dotenv import load_dotenv

load_dotenv() 
# --- Interface do Streamlit ---
st.set_page_config(page_title="Cadastro de Obrigação", layout="centered")

st.title("Sistema de Cadastro de Obrigação")

st.markdown("""
Este formulário permite inserir novas obrigações no banco de dados.
Preencha os campos abaixo e clique em "Salvar Obrigação".
""")

# Formulário de entrada de dados
with st.form("obrigacao_form", clear_on_submit=True):
    st.subheader("Dados da Obrigação")

    col1, col2 = st.columns(2)
    with col1:
        id_processo = st.number_input("ID do Processo", min_value=1, step=1, value=1)
        id_composicao_pauta = st.number_input("ID da Composição da Pauta", min_value=1, step=1, value=1)
        id_voto_pauta = st.number_input("ID do Voto da Pauta", min_value=1, step=1, value=1)
    with col2:
        descricao_obrigacao = st.text_area("Descrição da Obrigação", height=100)
        de_fazer = st.checkbox("É Obrigação de Fazer?", value=True)
        prazo = st.text_input("Prazo (ex: '30 dias', 'imediatamente')", value="")
        data_cumprimento = st.date_input("Data de Cumprimento", value=None, format="DD/MM/YYYY")

    st.subheader("Responsável e Multa Cominatória")
    col3, col4 = st.columns(2)
    with col3:
        orgao_responsavel = st.text_input("Órgão Responsável", value="")
        id_orgao_responsavel = st.number_input("ID do Órgão Responsável", min_value=0, step=1, value=0)
    with col4:
        tem_multa_cominatoria = st.checkbox("Tem Multa Cominatória?", value=False)

    if tem_multa_cominatoria:
        col5, col6 = st.columns(2)
        with col5:
            nome_responsavel_multa = st.text_input("Nome do Responsável pela Multa", value="")
            documento_responsavel_multa = st.text_input("Documento do Responsável pela Multa", value="")
            id_pessoa_multa = st.number_input("ID da Pessoa da Multa", min_value=0, step=1, value=0)
        with col6:
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
                solidarios_multa = None # Define como None para evitar erro na inserção

    submitted = st.form_submit_button("Salvar Obrigação")

    if submitted:
        if not descricao_obrigacao:
            st.error("A 'Descrição da Obrigação' é um campo obrigatório.")
        else:
            try:
                db_session = next(get_db()) # Obtém a sessão do banco de dados

                new_obrigacao = ObrigacaoORM(
                    IdProcesso=id_processo,
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

                db_session.add(new_obrigacao)
                db_session.commit()
                db_session.refresh(new_obrigacao) # Atualiza o objeto com o ID gerado

                st.success(f"Obrigação com ID {new_obrigacao.IdObrigacao} salva com sucesso!")

            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar a obrigação: {e}")
                st.exception(e) # Exibe o traceback completo para depuração

# --- Exibir dados existentes (opcional, para ver o que foi salvo) ---
st.markdown("---")
st.subheader("Obrigações Salvas (apenas para o banco de dados em memória)")

db_session_display = next(get_db())
obrigações = db_session_display.query(ObrigacaoORM).all()

if obrigações:
    st.write(f"Total de obrigações: {len(obrigações)}")
    for ob in obrigações:
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

