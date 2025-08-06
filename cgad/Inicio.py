import streamlit as st


st.set_page_config(
    page_title="Coordenadoria de Controle de Decisões",
    layout="centered"
)

st.title("Coordenadoria de Controle de Decisões")

st.markdown("""
Bem-vindo ao sistema da Coordenadoria de Controle de Decisões.
Use as opções abaixo para navegar pelas funcionalidades disponíveis.
""")

st.markdown("---")

st.subheader("Funcionalidades")

# Botão para a página de Cadastro de Obrigação
st.page_link("pages/CGR.py", label="Cadastro Geral de Recomendações (CGR - Recomendações)", icon="📝")



st.markdown("---")

st.info("Selecione uma funcionalidade no menu lateral ou através dos botões acima.")