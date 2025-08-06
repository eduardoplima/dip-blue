import os
import datetime
import json
import streamlit as st

from tools.models import ObrigacaoORM, ProcessoORM, DecisaoORM, RecomendacaoORM, get_db_dip, get_db_processo
from utils import extract_decisao_ner, extract_obrigacao
from dotenv import load_dotenv

import pickle

load_dotenv()

st.set_page_config(page_title="Cadastro de Obrigação", layout="centered")

st.title("Cadastro Geral de Recomendações (CGR) - Recomendações e Obrigações")

st.markdown(
"""
Este formulário permite registrar novas recomendações ou obrigações no sistema, conforme disposto no art. 431 do Regimento Interno do TCE/RN, 
que institui o Cadastro Geral de Recomendações (CGR).
Preencha os campos abaixo e clique em "Salvar" para efetivar o registro no banco de dados.
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
    #result = extract_decisao_ner(acordao)
    result = pickle.load(open("decisao_extraida.pkl", "rb")) if os.path.exists("decisao_extraida.pkl") else None
    if result:
        st.session_state.decisao_extraida = result
        st.success("Decisão extraída com sucesso!")
    else:
        st.error("Não foi possível extrair a decisão do acórdão.")

def salvar_obrigacao(obr_dict):
    id_processo = obr_dict.get("id_processo")
    id_composicao_pauta = obr_dict.get("id_composicao_pauta")
    id_voto_pauta = obr_dict.get("id_voto_pauta")
    de_fazer = obr_dict.get("de_fazer")
    prazo = obr_dict.get("prazo")
    data_cumprimento = obr_dict.get("data_cumprimento")
    id_orgao_responsavel = obr_dict.get("id_orgao_responsavel", 0)
    tem_multa_cominatoria = obr_dict.get("tem_multa_cominatoria", False)
    descricao_obrigacao = obr_dict.get("descricao_obrigacao")
    nome_responsavel_multa = obr_dict.get("nome_responsavel_multa")
    documento_responsavel_multa = obr_dict.get("documento_responsavel_multa")
    id_pessoa_multa = obr_dict.get("id_pessoa_multa", 0)
    valor_multa = obr_dict.get("valor_multa", 0.0)
    periodo_multa = obr_dict.get("periodo_multa")
    e_multa_solidaria = obr_dict.get("e_multa_solidaria", False)
    solidarios_multa = obr_dict.get("solidarios_multa", {})

    try:
        db_dip = next(get_db_dip())
        new_obrigacao = ObrigacaoORM(
            IdProcesso=id_processo,
            IdComposicaoPauta=id_composicao_pauta,
            IdVotoPauta=id_voto_pauta,
            DescricaoObrigacao=descricao_obrigacao,
            DeFazer=de_fazer,
            Prazo=prazo,
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

def salvar_recomendacao(rec_dict):
    id_processo = rec_dict.get("id_processo")
    id_composicao_pauta = rec_dict.get("id_composicao_pauta")
    id_voto_pauta = rec_dict.get("id_voto_pauta")
    descricao_recomendacao = rec_dict.get("descricao_recomendacao")
    prazo_cumprimento_recomendacao = rec_dict.get("prazo_cumprimento_recomendacao")
    data_cumprimento_recomendacao = rec_dict.get("data_cumprimento_recomendacao")
    nome_responsavel = rec_dict.get("nome_responsavel")
    id_pessoa_responsavel = rec_dict.get("id_pessoa_responsavel", 0)
    orgao_responsavel = rec_dict.get("orgao_responsavel")
    id_orgao_responsavel = rec_dict.get("id_orgao_responsavel", 0)

    try:
        db_dip = next(get_db_dip())
        new_recomendacao = RecomendacaoORM(
            IdProcesso=id_processo,
            IdComposicaoPauta=id_composicao_pauta,
            IdVotoPauta=id_voto_pauta,
            DescricaoRecomendacao=descricao_recomendacao,
            PrazoCumprimentoRecomendacao=prazo_cumprimento_recomendacao,
            DataCumprimentoRecomendacao=data_cumprimento_recomendacao if data_cumprimento_recomendacao else None,
            NomeResponsavel=nome_responsavel,
            IdPessoaResponsavel=id_pessoa_responsavel if id_pessoa_responsavel > 0 else None,
            OrgaoResponsavel=orgao_responsavel,
            IdOrgaoResponsavel=id_orgao_responsavel if id_orgao_responsavel > 0 else None,
        )
        db_dip.add(new_recomendacao)
        db_dip.commit()
        db_dip.refresh(new_recomendacao)

        if "recomendacoes_salvas" not in st.session_state:
            st.session_state.recomendacoes_salvas = []
        st.session_state.recomendacoes_salvas.append(new_recomendacao)
        st.success(f"Recomendação com ID {new_recomendacao.IdRecomendacao} salva com sucesso!")

    except Exception as e:
        st.error(f"Ocorreu um erro ao salvar a recomendação: {e}")
        st.exception(e)

    finally:
        db_dip.close()
    

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
    decisao_extraida = st.session_state.decisao_extraida

    st.subheader("Obrigações Extraídas")
    for i, o in enumerate(decisao_extraida.obrigacoes):
        with st.form(key=f"obrigacao_form_{i}", clear_on_submit=True):
            st.markdown(f"**Obrigação {i+1}:**")
            
            # Campos da obrigação
            descricao_obrigacao = st.text_area(
                "Descrição da Obrigação", 
                value=o.descricao_obrigacao, 
                height=100,
                key=f"descricao_obr_{i}"
            )
            '''
            de_fazer = st.checkbox(
                "É Obrigação de Fazer?", 
                value=o.de_fazer,
                key=f"de_fazer_obr_{i}"
            )
            prazo = st.text_input(
                "Prazo (ex: '30 dias', 'imediatamente')", 
                value=o.prazo,
                key=f"prazo_obr_{i}"
            )
            data_cumprimento = st.date_input(
                "Data de Cumprimento", 
                value=o.data_cumprimento if o.data_cumprimento else None, 
                format="DD/MM/YYYY",
                key=f"data_cumprimento_obr_{i}"
            )

            st.subheader("Responsável e Multa Cominatória")
            orgao_responsavel = st.text_input(
                "Órgão Responsável", 
                value=o.orgao_responsavel,
                key=f"orgao_resp_obr_{i}"
            )
            id_orgao_responsavel = st.number_input(
                "ID do Órgão Responsável", 
                min_value=0, 
                step=1, 
                value=o.id_orgao_responsavel if o.id_orgao_responsavel else 0,
                key=f"id_orgao_resp_obr_{i}"
            )
            tem_multa_cominatoria = st.checkbox(
                "Tem Multa Cominatória?", 
                value=o.tem_multa_cominatoria,
                key=f"tem_multa_obr_{i}"
            )

            if tem_multa_cominatoria:
                nome_responsavel_multa = st.text_input(
                    "Nome do Responsável pela Multa", 
                    value=o.nome_responsavel_multa,
                    key=f"nome_multa_obr_{i}"
                )
                documento_responsavel_multa = st.text_input(
                    "Documento do Responsável pela Multa", 
                    value=o.documento_responsavel_multa,
                    key=f"doc_multa_obr_{i}"
                )
                id_pessoa_multa = st.number_input(
                    "ID da Pessoa da Multa", 
                    min_value=0, 
                    step=1, 
                    value=o.id_pessoa_multa if o.id_pessoa_multa else 0,
                    key=f"id_pessoa_multa_obr_{i}"
                )
                valor_multa = st.number_input(
                    "Valor da Multa Cominatória", 
                    min_value=0.0, 
                    step=0.01, 
                    value=o.valor_multa if o.valor_multa else 0.0,
                    key=f"valor_multa_obr_{i}"
                )
                periodo_multa = st.text_input(
                    "Período da Multa", 
                    value=o.periodo_multa,
                    key=f"periodo_multa_obr_{i}"
                )
                e_multa_solidaria = st.checkbox(
                    "É Multa Cominatória Solidária?", 
                    value=o.e_multa_solidaria,
                    key=f"multa_solidaria_obr_{i}"
                )
                solidarios_multa = {}
                if e_multa_solidaria:
                    solidarios_multa_input = st.text_area(
                        "Solidários da Multa (JSON)", 
                        height=100, 
                        value=json.dumps(o.solidarios_multa),
                        key=f"solidarios_multa_obr_{i}"
                    )
                    try:
                        if solidarios_multa_input:
                            solidarios_multa = json.loads(solidarios_multa_input)
                    except json.JSONDecodeError:
                        st.error("Formato JSON inválido para 'Solidários da Multa Cominatória'.")
                        solidarios_multa = None
                    '''

            submitted_obr = st.form_submit_button("Salvar Obrigação")
            
            if submitted_obr:
                '''
                obr_dict = {
                    "id_processo": decisao_extraida.id_processo,
                    "id_composicao_pauta": decisao_extraida.id_composicao_pauta,
                    "id_voto_pauta": decisao_extraida.id_voto_pauta,
                    "descricao_obrigacao": descricao_obrigacao,
                    "de_fazer": de_fazer,
                    "prazo": prazo,
                    "data_cumprimento": data_cumprimento,
                    "orgao_responsavel": orgao_responsavel,
                    "id_orgao_responsavel": id_orgao_responsavel,
                    "tem_multa_cominatoria": tem_multa_cominatoria,
                    "nome_responsavel_multa": nome_responsavel_multa if tem_multa_cominatoria else None,
                    "documento_responsavel_multa": documento_responsavel_multa if tem_multa_cominatoria else None,
                    "id_pessoa_multa": id_pessoa_multa if tem_multa_cominatoria else None,
                    "valor_multa": valor_multa if tem_multa_cominatoria else None,
                    "periodo_multa": periodo_multa if tem_multa_cominatoria else None,
                    "e_multa_solidaria": e_multa_solidaria if tem_multa_cominatoria else False,
                    "solidarios_multa": solidarios_multa if tem_multa_cominatoria and e_multa_solidaria else None,
                }
                '''
                obr_dict = {
                    "descricao_obrigacao": descricao_obrigacao
                }
                salvar_obrigacao(obr_dict)

    st.subheader("Recomendações Extraídas")
    for i, r in enumerate(decisao_extraida.recomendacoes):
        with st.form(key=f"recomendacao_form_{i}", clear_on_submit=True):
            st.markdown(f"**Recomendação {i+1}:**")
            
            # Campos da recomendação
            descricao_recomendacao = st.text_area(
                "Descrição da Recomendação", 
                value=r.descricao_recomendacao, 
                height=100,
                key=f"descricao_rec_{i}"
            )
            '''
            prazo_cumprimento_recomendacao = st.text_input(
                "Prazo sugerido", 
                value=r.prazo_cumprimento_recomendacao,
                key=f"prazo_rec_{i}"
            )
            data_cumprimento_recomendacao = st.date_input(
                "Data de cumprimento", 
                value=r.data_cumprimento_recomendacao if r.data_cumprimento_recomendacao else None,
                format="DD/MM/YYYY",
                key=f"data_rec_{i}"
            )
            nome_responsavel = st.text_input(
                "Nome do Responsável", 
                value=r.nome_responsavel_recomendacao,
                key=f"nome_resp_rec_{i}"
            )
            orgao_responsavel = st.text_input(
                "Órgão Responsável", 
                value=r.orgao_responsavel_recomendacao,
                key=f"orgao_resp_rec_{i}"
            )
            '''

            submitted_rec = st.form_submit_button("Salvar Recomendação")
            
            if submitted_rec:
                '''
                rec_dict = {
                    "id_processo": decisao_extraida.id_processo,
                    "id_composicao_pauta": decisao_extraida.id_composicao_pauta,
                    "id_voto_pauta": decisao_extraida.id_voto_pauta,
                    "descricao_recomendacao": descricao_recomendacao,
                    "prazo_cumprimento_recomendacao": prazo_cumprimento_recomendacao,
                    "data_cumprimento_recomendacao": data_cumprimento_recomendacao,
                    "nome_responsavel": nome_responsavel,
                    "orgao_responsavel": orgao_responsavel,
                    "id_pessoa_responsavel": None, # Adicione lógica para isso se necessário
                    "id_orgao_responsavel": None, # Adicione lógica para isso se necessário
                }
                '''
                rec_dict = {
                    "descricao_recomendacao": descricao_recomendacao
                }
                salvar_recomendacao(rec_dict)
            

st.markdown("---")
st.subheader("Obrigações salvas nessa sessão")

db_session_display = next(get_db_dip())
obrigacoes = st.session_state.get("obrigacoes_salvas", [])

if obrigacoes:
    st.write(f"Total de obrigações: {len(obrigacoes)}")
    for ob in obrigacoes:
        st.json({
            "DescricaoObrigacao": ob.DescricaoObrigacao,
            "DeFazer": ob.DeFazer,
            "DataCumprimento": str(ob.DataCumprimento) if ob.DataCumprimento else None,
            "TemMultaCominatoria": ob.TemMultaCominatoria,
            "ValorMultaCominatoria": ob.ValorMultaCominatoria,
            "SolidariosMultaCominatoria": ob.SolidariosMultaCominatoria
        })
else:
    st.info("Nenhuma obrigação salva ainda.")