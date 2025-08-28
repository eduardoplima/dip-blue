import streamlit as st
import datetime
import pandas as pd
import json
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
    get_pessoas_str,
    to_str_or_none,
    to_date_or_none,
    to_bool,
    to_float,
    to_pos_int_or_none,
    get_orgaos,
    get_pessoas
)
# Acesso a `Literal` para as opções de Período da Multa
from tools.schema import Obrigacao, Recomendacao

st.set_page_config(page_title="Cancelamento e Alteração de Itens", layout="centered")

st.title("Cancelamento e Alteração de Obrigações e Recomendações")

st.markdown(
    """
    Use este formulário para buscar um processo e gerenciar as obrigações e recomendações cadastradas.
    Você pode cancelar ou alterar os itens existentes.
    """
)


def buscar_processo():
    numero_processo = st.session_state.get("numero_processo_input")
    ano_processo = st.session_state.get("ano_processo_input")

    if not numero_processo or not ano_processo:
        st.error("Por favor, preencha o número e o ano do processo.")
        st.session_state.processo_encontrado = None
        st.session_state.obrigacoes_processo = None
        st.session_state.recomendacoes_processo = None
        return
    
    df_decisao = get_df_decisao(numero_processo, ano_processo)
    
    if df_decisao.empty:
        st.warning("O processo informado não possui decisões ou não existe.")
        st.session_state.processo_encontrado = None
        st.session_state.obrigacoes_processo = None
        st.session_state.recomendacoes_processo = None
        return
    
    st.session_state.processo_encontrado = df_decisao.iloc[0]
    id_processo = st.session_state.processo_encontrado['id_processo']
    
    db_dip = next(get_db_dip())
    try:
        obr_result = db_dip.query(ObrigacaoORM).filter(ObrigacaoORM.IdProcesso == int(id_processo)).all()
        rec_result = db_dip.query(RecomendacaoORM).filter(RecomendacaoORM.IdProcesso == int(id_processo)).all()
        st.session_state.obrigacoes_processo = obr_result
        st.session_state.recomendacoes_processo = rec_result
    except Exception as e:
        st.error(f"Erro ao buscar obrigações e recomendações: {e}")
        st.exception(e)
    finally:
        db_dip.close()

def salvar_cancelamento_obrigacao(id_obrigacao, motivo):
    try:
        db_dip = next(get_db_dip())
        
        obrigacao = db_dip.query(ObrigacaoORM).filter(ObrigacaoORM.IdObrigacao == id_obrigacao).first()
        if not obrigacao:
            st.error("Obrigação não encontrada.")
            return

        if obrigacao.Cancelado:
            st.warning(f"A Obrigação com ID {id_obrigacao} já foi cancelada anteriormente.")
            return

        cancelamento = CancelamentoObrigacao(
            IdObrigacao=id_obrigacao,
            MotivoCancelamento=motivo,
            DataCancelamento=datetime.date.today()
        )
        db_dip.add(cancelamento)
        
        obrigacao.Cancelado = True
        db_dip.add(obrigacao)

        db_dip.commit()
        st.success(f"Obrigação com ID {id_obrigacao} cancelada com sucesso!")
        buscar_processo()
    except Exception as e:
        st.error(f"Ocorreu um erro ao cancelar a obrigação: {e}")
        st.exception(e)
    finally:
        db_dip.close()

def salvar_cancelamento_recomendacao(id_recomendacao, motivo):
    try:
        db_dip = next(get_db_dip())

        recomendacao = db_dip.query(RecomendacaoORM).filter(RecomendacaoORM.IdRecomendacao == id_recomendacao).first()
        if not recomendacao:
            st.error("Recomendação não encontrada.")
            return

        if recomendacao.Cancelado:
            st.warning(f"A Recomendação com ID {id_recomendacao} já foi cancelada anteriormente.")
            return

        cancelamento = CancelamentoRecomendacao(
            IdRecomendacao=id_recomendacao,
            MotivoCancelamento=motivo,
            DataCancelamento=datetime.date.today()
        )
        db_dip.add(cancelamento)

        recomendacao.Cancelado = True
        db_dip.add(recomendacao)

        db_dip.commit()
        st.success(f"Recomendação com ID {id_recomendacao} cancelada com sucesso!")
        buscar_processo()
    except Exception as e:
        st.error(f"Ocorreu um erro ao cancelar a recomendação: {e}")
        st.exception(e)
    finally:
        db_dip.close()

def salvar_alteracao_obrigacao(id_obrigacao, **kwargs):
    try:
        db_dip = next(get_db_dip())
        obrigacao = db_dip.query(ObrigacaoORM).filter(ObrigacaoORM.IdObrigacao == id_obrigacao).first()
        if not obrigacao:
            st.error("Obrigação não encontrada para alteração.")
            return

        # Atualizar os campos com os valores do formulário
        obrigacao.DescricaoObrigacao = to_str_or_none(kwargs.get('descricao_obrigacao'))
        obrigacao.DeFazer = to_bool(kwargs.get('de_fazer'))
        obrigacao.Prazo = to_str_or_none(kwargs.get('prazo'))
        obrigacao.DataCumprimento = to_date_or_none(kwargs.get('data_cumprimento'))
        obrigacao.OrgaoResponsavel = to_str_or_none(kwargs.get('orgao_responsavel'))
        obrigacao.IdOrgaoResponsavel = to_pos_int_or_none(kwargs.get('id_orgao_responsavel'))
        obrigacao.TemMultaCominatoria = to_bool(kwargs.get('tem_multa_cominatoria'))
        if obrigacao.TemMultaCominatoria:
            obrigacao.NomeResponsavelMultaCominatoria = to_str_or_none(kwargs.get('nome_responsavel_multa_cominatoria'))
            obrigacao.DocumentoResponsavelMultaCominatoria = to_str_or_none(kwargs.get('documento_responsavel_multa_cominatoria'))
            obrigacao.IdPessoaMultaCominatoria = to_pos_int_or_none(kwargs.get('id_pessoa_multa_cominatoria'))
            obrigacao.ValorMultaCominatoria = to_float(kwargs.get('valor_multa_cominatoria'))
            obrigacao.PeriodoMultaCominatoria = to_str_or_none(kwargs.get('periodo_multa_cominatoria'))
            obrigacao.EMultaCominatoriaSolidaria = to_bool(kwargs.get('e_multa_cominatoria_solidaria'))
            solidarios = kwargs.get('solidarios_multa_cominatoria')
            if isinstance(solidarios, str):
                try:
                    obrigacao.SolidariosMultaCominatoria = json.loads(solidarios)
                except json.JSONDecodeError:
                    st.error("Formato JSON inválido para 'Solidários da Multa Cominatória'.")
                    return
        else:
            obrigacao.NomeResponsavelMultaCominatoria = None
            obrigacao.DocumentoResponsavelMultaCominatoria = None
            obrigacao.IdPessoaMultaCominatoria = None
            obrigacao.ValorMultaCominatoria = None
            obrigacao.PeriodoMultaCominatoria = None
            obrigacao.EMultaCominatoriaSolidaria = False
            obrigacao.SolidariosMultaCominatoria = None
        
        db_dip.commit()
        st.success(f"Obrigação com ID {id_obrigacao} alterada com sucesso!")
        buscar_processo()
    except Exception as e:
        st.error(f"Ocorreu um erro ao alterar a obrigação: {e}")
        st.exception(e)
    finally:
        db_dip.close()

def salvar_alteracao_recomendacao(id_recomendacao, **kwargs):
    try:
        db_dip = next(get_db_dip())
        recomendacao = db_dip.query(RecomendacaoORM).filter(RecomendacaoORM.IdRecomendacao == id_recomendacao).first()
        if not recomendacao:
            st.error("Recomendação não encontrada para alteração.")
            return

        # Atualizar os campos com os valores do formulário
        recomendacao.DescricaoRecomendacao = to_str_or_none(kwargs.get('descricao_recomendacao'))
        recomendacao.PrazoCumprimentoRecomendacao = to_str_or_none(kwargs.get('prazo_cumprimento_recomendacao'))
        recomendacao.DataCumprimentoRecomendacao = to_date_or_none(kwargs.get('data_cumprimento_recomendacao'))
        recomendacao.NomeResponsavel = to_str_or_none(kwargs.get('nome_responsavel'))
        recomendacao.IdPessoaResponsavel = to_pos_int_or_none(kwargs.get('id_pessoa_responsavel'))
        recomendacao.OrgaoResponsavel = to_str_or_none(kwargs.get('orgao_responsavel'))
        recomendacao.IdOrgaoResponsavel = to_pos_int_or_none(kwargs.get('id_orgao_responsavel'))
        
        db_dip.commit()
        st.success(f"Recomendação com ID {id_recomendacao} alterada com sucesso!")
        buscar_processo()
    except Exception as e:
        st.error(f"Ocorreu um erro ao alterar a recomendação: {e}")
        st.exception(e)
    finally:
        db_dip.close()

def mask_input_on_blur():
    raw_value = st.session_state.numero_processo_input
    if raw_value:
        st.session_state.numero_processo_input = raw_value.zfill(6)

col1_busca, col2_busca, col_btn_busca = st.columns([1, 1, 0.5])
with col1_busca:
    st.text_input("Número do Processo", key="numero_processo_input", on_change=mask_input_on_blur)
with col2_busca:
    st.text_input("Ano do Processo", key="ano_processo_input")
with col_btn_busca:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Buscar", on_click=buscar_processo)

processo = st.session_state.get("processo_encontrado", None)
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
            status = '(CANCELADA)' if ob.Cancelado else '(ATIVA)'
            with st.expander(f"Obrigação {ob.IdObrigacao} {status}"):
                
                # Exibição dos dados atuais
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
                    st.markdown("---")
                    st.markdown("##### Gerenciar Obrigação")
                    with st.form(key=f"cancelar_obr_form_{ob.IdObrigacao}", clear_on_submit=True):
                        st.markdown("**Cancelar Obrigação**")
                        motivo_obr = st.text_area("Motivo", key=f"motivo_obr_{ob.IdObrigacao}")
                        submitted_obr_cancel = st.form_submit_button("Confirmar Cancelamento")
                        if submitted_obr_cancel:
                            if not motivo_obr:
                                st.error("O motivo do cancelamento é obrigatório.")
                            else:
                                salvar_cancelamento_obrigacao(ob.IdObrigacao, motivo_obr)
                    with st.form(key=f"alterar_obr_form_{ob.IdObrigacao}", clear_on_submit=False):
                        st.markdown("**Alterar Obrigação**")
                        novo_descricao = st.text_area("Descrição", value=ob.DescricaoObrigacao, key=f"alterar_desc_obr_{ob.IdObrigacao}")
                        novo_de_fazer = st.checkbox("É Obrigação de Fazer?", value=ob.DeFazer, key=f"alterar_de_fazer_obr_{ob.IdObrigacao}")
                        novo_prazo = st.text_input("Prazo", value=ob.Prazo if ob.Prazo else "", key=f"alterar_prazo_obr_{ob.IdObrigacao}")
                        novo_data_cumprimento = st.date_input("Data de Cumprimento", value=ob.DataCumprimento, format="DD/MM/YYYY", key=f"alterar_data_cumprimento_obr_{ob.IdObrigacao}")

                        orgaos_df = get_orgaos()
                        opcoes_orgaos = orgaos_df.to_dict("records")
                        try:
                            index_orgao = next(i for i, o in enumerate(opcoes_orgaos) if o['nome'] == ob.OrgaoResponsavel)
                        except StopIteration:
                            index_orgao = 0
                        novo_orgao_selecionado = st.selectbox("Órgão Responsável", options=opcoes_orgaos, index=index_orgao, format_func=lambda x: x['nome'], key=f"alterar_orgao_resp_obr_{ob.IdObrigacao}")
                        novo_id_orgao = novo_orgao_selecionado['id']
                        
                        st.subheader("Multa Cominatória")
                        novo_tem_multa = st.checkbox("Tem Multa Cominatória?", value=ob.TemMultaCominatoria, key=f"alterar_tem_multa_{ob.IdObrigacao}")
                        
                        if novo_tem_multa:
                            novo_nome_responsavel_multa = st.text_input("Nome do Responsável pela Multa", value=ob.NomeResponsavelMultaCominatoria if ob.NomeResponsavelMultaCominatoria else "", key=f"alterar_nome_resp_multa_{ob.IdObrigacao}")
                            novo_doc_responsavel_multa = st.text_input("Documento do Responsável pela Multa", value=ob.DocumentoResponsavelMultaCominatoria if ob.DocumentoResponsavelMultaCominatoria else "", key=f"alterar_doc_resp_multa_{ob.IdObrigacao}")
                            novo_id_pessoa_multa = st.number_input("ID da Pessoa da Multa", min_value=0, step=1, value=ob.IdPessoaMultaCominatoria if ob.IdPessoaMultaCominatoria else 0, key=f"alterar_id_pessoa_multa_{ob.IdObrigacao}")
                            novo_valor_multa = st.number_input("Valor da Multa Cominatória", min_value=0.0, step=0.01, value=ob.ValorMultaCominatoria if ob.ValorMultaCominatoria else 0.0, key=f"alterar_valor_multa_{ob.IdObrigacao}")
                            periodo_options = ["horário", "diário", "semanal", "mensal"]
                            try:
                                current_periodo_index = periodo_options.index(ob.PeriodoMultaCominatoria)
                            except ValueError:
                                current_periodo_index = 0
                            novo_periodo_multa = st.selectbox("Período da Multa Cominatória", options=periodo_options, index=current_periodo_index, key=f"alterar_periodo_multa_{ob.IdObrigacao}")
                            novo_e_multa_solidaria = st.checkbox("É Multa Cominatória Solidária?", value=ob.EMultaCominatoriaSolidaria, key=f"alterar_multa_solidaria_{ob.IdObrigacao}")
                            
                            novo_solidarios_multa = {}
                            if novo_e_multa_solidaria:
                                solidarios_value = json.dumps(ob.SolidariosMultaCominatoria) if ob.SolidariosMultaCominatoria else ""
                                novo_solidarios_multa = st.text_area("Solidários da Multa (JSON)", height=100, value=solidarios_value, key=f"alterar_solidarios_multa_{ob.IdObrigacao}")

                        submitted_obr_alterar = st.form_submit_button("Confirmar Alteração")
                        if submitted_obr_alterar:
                            salvar_alteracao_obrigacao(
                                ob.IdObrigacao,
                                descricao_obrigacao=novo_descricao,
                                de_fazer=novo_de_fazer,
                                prazo=novo_prazo,
                                data_cumprimento=novo_data_cumprimento,
                                orgao_responsavel=novo_orgao_selecionado['nome'],
                                id_orgao_responsavel=novo_id_orgao,
                                tem_multa_cominatoria=novo_tem_multa,
                                nome_responsavel_multa_cominatoria=novo_nome_responsavel_multa if novo_tem_multa else None,
                                documento_responsavel_multa_cominatoria=novo_doc_responsavel_multa if novo_tem_multa else None,
                                id_pessoa_multa_cominatoria=novo_id_pessoa_multa if novo_tem_multa else None,
                                valor_multa_cominatoria=novo_valor_multa if novo_tem_multa else None,
                                periodo_multa_cominatoria=novo_periodo_multa if novo_tem_multa else None,
                                e_multa_cominatoria_solidaria=novo_e_multa_solidaria if novo_tem_multa else False,
                                solidarios_multa_cominatoria=novo_solidarios_multa if novo_tem_multa and novo_e_multa_solidaria else None,
                            )
    else:
        st.info("Nenhuma obrigação encontrada para este processo.")

    st.subheader("Recomendações cadastradas")
    recomendacoes = st.session_state.get("recomendacoes_processo", [])
    if recomendacoes:
        for i, rec in enumerate(recomendacoes):
            status = '(CANCELADA)' if rec.Cancelado else '(ATIVA)'
            with st.expander(f"Recomendação {rec.IdRecomendacao} {status}"):
                
                # Exibição dos dados atuais
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
                    st.markdown("---")
                    st.markdown("##### Gerenciar Recomendação")
                    with st.form(key=f"cancelar_rec_form_{rec.IdRecomendacao}", clear_on_submit=True):
                        st.markdown("**Cancelar Recomendação**")
                        motivo_rec = st.text_area("Motivo", key=f"motivo_rec_{rec.IdRecomendacao}")
                        submitted_rec_cancel = st.form_submit_button("Confirmar Cancelamento")
                        if submitted_rec_cancel:
                            if not motivo_rec:
                                st.error("O motivo do cancelamento é obrigatório.")
                            else:
                                salvar_cancelamento_recomendacao(rec.IdRecomendacao, motivo_rec)
                    with st.form(key=f"alterar_rec_form_{rec.IdRecomendacao}", clear_on_submit=False):
                        st.markdown("**Alterar Recomendação**")
                        novo_descricao = st.text_area("Descrição", value=rec.DescricaoRecomendacao, key=f"alterar_desc_rec_{rec.IdRecomendacao}")
                        novo_prazo = st.text_input("Prazo", value=rec.PrazoCumprimentoRecomendacao if rec.PrazoCumprimentoRecomendacao else "", key=f"alterar_prazo_rec_{rec.IdRecomendacao}")
                        novo_data_cumprimento = st.date_input("Data de cumprimento", value=rec.DataCumprimentoRecomendacao, format="DD/MM/YYYY", key=f"alterar_data_rec_{rec.IdRecomendacao}")

                        pessoas_df = get_pessoas()
                        opcoes_pessoas = pessoas_df.to_dict("records")
                        try:
                            index_pessoa = next(i for i, p in enumerate(opcoes_pessoas) if p['nome'] == rec.NomeResponsavel)
                        except StopIteration:
                            index_pessoa = 0
                        nova_pessoa_selecionada = st.selectbox("Nome do Responsável", options=opcoes_pessoas, index=index_pessoa, format_func=lambda x: x['nome'], key=f"alterar_nome_resp_rec_{rec.IdRecomendacao}")
                        novo_id_pessoa = nova_pessoa_selecionada['id']
                        
                        orgaos_df = get_orgaos()
                        opcoes_orgaos = orgaos_df.to_dict("records")
                        try:
                            index_orgao = next(i for i, o in enumerate(opcoes_orgaos) if o['nome'] == rec.OrgaoResponsavel)
                        except StopIteration:
                            index_orgao = 0
                        novo_orgao_selecionado = st.selectbox("Órgão Responsável", options=opcoes_orgaos, index=index_orgao, format_func=lambda x: x['nome'], key=f"alterar_orgao_resp_rec_{rec.IdRecomendacao}")
                        novo_id_orgao = novo_orgao_selecionado['id']
                        
                        submitted_rec_alterar = st.form_submit_button("Confirmar Alteração")
                        if submitted_rec_alterar:
                            salvar_alteracao_recomendacao(
                                rec.IdRecomendacao,
                                descricao_recomendacao=novo_descricao,
                                prazo_cumprimento_recomendacao=novo_prazo,
                                data_cumprimento_recomendacao=novo_data_cumprimento,
                                nome_responsavel=nova_pessoa_selecionada['nome'],
                                id_pessoa_responsavel=novo_id_pessoa,
                                orgao_responsavel=novo_orgao_selecionado['nome'],
                                id_orgao_responsavel=novo_id_orgao
                            )
    else:
        st.info("Nenhuma recomendação encontrada para este processo.")