import streamlit as st
import datetime
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from tools.models import (
    ObrigacaoORM, 
    RecomendacaoORM, 
    CancelamentoObrigacao, 
    CancelamentoRecomendacao, 
    engine_dip,
    get_db_dip,
    BaseDIP
)
from utils import (
    get_df_decisao, 
    get_pessoas_str
)

st.set_page_config(page_title="Cancelamento de Itens", layout="centered")

st.title("Cancelamento de Obrigações e Recomendações")

st.markdown(
    """
    Use este formulário para registrar o cancelamento de uma obrigação ou recomendação.
    Busque o processo, selecione o item desejado e insira o motivo do cancelamento.
    A data de cancelamento será registrada automaticamente.
    """
)

def buscar_processo():
    numero_processo = st.session_state.get("numero_processo_cancelamento_input")
    ano_processo = st.session_state.get("ano_processo_cancelamento_input")

    if not numero_processo or not ano_processo:
        st.error("Por favor, preencha o número e o ano do processo.")
        st.session_state.processo_encontrado_cancelamento = None
        st.session_state.obrigacoes_processo = None
        st.session_state.recomendacoes_processo = None
        return
    
    df_decisao = get_df_decisao(numero_processo, ano_processo)
    
    if df_decisao.empty:
        st.warning("O processo informado não possui decisões ou não existe.")
        st.session_state.processo_encontrado_cancelamento = None
        st.session_state.obrigacoes_processo = None
        st.session_state.recomendacoes_processo = None
        return
    
    st.session_state.processo_encontrado_cancelamento = df_decisao.iloc[0]
    id_processo = st.session_state.processo_encontrado_cancelamento['id_processo']
    
    db_dip = next(get_db_dip())
    try:
        obr_result = db_dip.query(ObrigacaoORM).filter(ObrigacaoORM.IdProcesso == int(id_processo)).all()
        rec_result = db_dip.query(RecomendacaoORM).filter(RecomendacaoORM.IdProcesso == int(id_processo)).all()
        st.session_state.obrigacoes_processo = obr_result
        st.session_state.recomendacoes_processo = rec_result
    except Exception as e:
        st.error(f"Erro ao buscar obrigações e recomendações: {e}")
    finally:
        db_dip.close()

def salvar_cancelamento_obrigacao(id_obrigacao, motivo):
    try:
        db_dip = next(get_db_dip())
        
        # Verificar se a obrigação já foi cancelada
        obrigacao = db_dip.query(ObrigacaoORM).filter(ObrigacaoORM.IdObrigacao == id_obrigacao).first()
        if obrigacao.Cancelado:
            st.warning(f"A Obrigação com ID {id_obrigacao} já foi cancelada anteriormente.")
            return

        cancelamento = CancelamentoObrigacao(
            IdObrigacao=id_obrigacao,
            MotivoCancelamento=motivo,
            DataCancelamento=datetime.date.today()
        )
        db_dip.add(cancelamento)
        
        # Marcar a obrigação como cancelada
        obrigacao.Cancelado = True
        db_dip.add(obrigacao)

        db_dip.commit()
        st.success(f"Obrigação com ID {id_obrigacao} cancelada com sucesso!")
        buscar_processo() # Atualiza a lista após o cancelamento
    except Exception as e:
        st.error(f"Ocorreu um erro ao cancelar a obrigação: {e}")
        st.exception(e)
    finally:
        db_dip.close()

def salvar_cancelamento_recomendacao(id_recomendacao, motivo):
    try:
        db_dip = next(get_db_dip())

        # Verificar se a recomendação já foi cancelada
        recomendacao = db_dip.query(RecomendacaoORM).filter(RecomendacaoORM.IdRecomendacao == id_recomendacao).first()
        if recomendacao.Cancelado:
            st.warning(f"A Recomendação com ID {id_recomendacao} já foi cancelada anteriormente.")
            return

        cancelamento = CancelamentoRecomendacao(
            IdRecomendacao=id_recomendacao,
            MotivoCancelamento=motivo,
            DataCancelamento=datetime.date.today()
        )
        db_dip.add(cancelamento)

        # Marcar a recomendação como cancelada
        recomendacao.Cancelado = True
        db_dip.add(recomendacao)

        db_dip.commit()
        st.success(f"Recomendação com ID {id_recomendacao} cancelada com sucesso!")
        buscar_processo() # Atualiza a lista após o cancelamento
    except Exception as e:
        st.error(f"Ocorreu um erro ao cancelar a recomendação: {e}")
        st.exception(e)
    finally:
        db_dip.close()

# Interface de busca
col1_busca, col2_busca, col_btn_busca = st.columns([1, 1, 0.5])
with col1_busca:
    st.text_input("Número do Processo", key="numero_processo_cancelamento_input")
with col2_busca:
    st.text_input("Ano do Processo", key="ano_processo_cancelamento_input")
with col_btn_busca:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Buscar", on_click=buscar_processo)

# Bloco para exibir os resultados da busca
processo = st.session_state.get("processo_encontrado_cancelamento", None)
if processo is not None:
    assunto = processo['assunto']
    orgao = processo['orgao_responsavel']
    responsaveis = get_pessoas_str(processo['responsaveis'])
    
    st.markdown("---")
    st.subheader(f"Processo encontrado: {processo['numero_processo']}/{processo['ano_processo']}")
    st.markdown(f"**Assunto:** {assunto}")
    st.markdown(f"**Órgão envolvido:** {orgao}")
    st.markdown(f"**Pessoas responsáveis:** {responsaveis}")

    st.subheader("Obrigações cadastradas")
    obrigacoes = st.session_state.get("obrigacoes_processo", [])
    if obrigacoes:
        for i, ob in enumerate(obrigacoes):
            with st.expander(f"Obrigação {ob.IdObrigacao} {'(CANCELADA)' if ob.Cancelado else ''}"):
                st.markdown(f"**Descrição:** {ob.DescricaoObrigacao}")
                st.markdown(f"**Prazo:** {ob.Prazo}")
                st.markdown(f"**Data de Cumprimento:** {ob.DataCumprimento}")
                st.markdown(f"**Responsável:** {ob.OrgaoResponsavel}")
                
                if ob.TemMultaCominatoria:
                    st.markdown("**Multa Cominatória:** Sim")
                    st.markdown(f"**Valor:** R$ {ob.ValorMultaCominatoria}")
                    st.markdown(f"**Responsável da Multa:** {ob.NomeResponsavelMultaCominatoria}")
                    st.markdown(f"**Documento do Responsável:** {ob.DocumentoResponsavelMultaCominatoria}")
                
                if ob.Cancelado:
                    db_dip = next(get_db_dip())
                    cancelado_info = db_dip.query(CancelamentoObrigacao).filter(CancelamentoObrigacao.IdObrigacao == ob.IdObrigacao).first()
                    db_dip.close()
                    st.info(f"Motivo do cancelamento: {cancelado_info.MotivoCancelamento}")
                    st.info(f"Data do cancelamento: {cancelado_info.DataCancelamento}")
                else:
                    with st.form(key=f"cancelar_obr_form_{ob.IdObrigacao}", clear_on_submit=True):
                        motivo_obr = st.text_area(f"Motivo para cancelar a Obrigação {ob.IdObrigacao}", key=f"motivo_obr_{ob.IdObrigacao}")
                        submitted_obr = st.form_submit_button("Confirmar Cancelamento")
                        if submitted_obr:
                            if not motivo_obr:
                                st.error("O motivo do cancelamento é obrigatório.")
                            else:
                                salvar_cancelamento_obrigacao(ob.IdObrigacao, motivo_obr)
    else:
        st.info("Nenhuma obrigação encontrada para este processo.")

    st.subheader("Recomendações cadastradas")
    recomendacoes = st.session_state.get("recomendacoes_processo", [])
    if recomendacoes:
        for i, rec in enumerate(recomendacoes):
            with st.expander(f"Recomendação {rec.IdRecomendacao} {'(CANCELADA)' if rec.Cancelado else ''}"):
                st.markdown(f"**Descrição:** {rec.DescricaoRecomendacao}")
                st.markdown(f"**Prazo:** {rec.PrazoCumprimentoRecomendacao}")
                st.markdown(f"**Data de Cumprimento:** {rec.DataCumprimentoRecomendacao}")
                st.markdown(f"**Responsável:** {rec.NomeResponsavel}")
                st.markdown(f"**Órgão Responsável:** {rec.OrgaoResponsavel}")

                if rec.Cancelado:
                    db_dip = next(get_db_dip())
                    cancelado_info = db_dip.query(CancelamentoRecomendacao).filter(CancelamentoRecomendacao.IdRecomendacao == rec.IdRecomendacao).first()
                    db_dip.close()
                    st.info(f"Motivo do cancelamento: {cancelado_info.MotivoCancelamento}")
                    st.info(f"Data do cancelamento: {cancelado_info.DataCancelamento}")
                else:
                    with st.form(key=f"cancelar_rec_form_{rec.IdRecomendacao}", clear_on_submit=True):
                        motivo_rec = st.text_area(f"Motivo para cancelar a Recomendação {rec.IdRecomendacao}", key=f"motivo_rec_{rec.IdRecomendacao}")
                        submitted_rec = st.form_submit_button("Confirmar Cancelamento")
                        if submitted_rec:
                            if not motivo_rec:
                                st.error("O motivo do cancelamento é obrigatório.")
                            else:
                                salvar_cancelamento_recomendacao(rec.IdRecomendacao, motivo_rec)
    else:
        st.info("Nenhuma recomendação encontrada para este processo.")