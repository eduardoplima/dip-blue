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
st.page_link("pages/cad_obrigacao.py", label="Cadastro de Obrigação", icon="📝")

# Botão para a página de Cadastro de Recomendação
st.page_link("pages/cad_recomendacao.py", label="Cadastro de Recomendação", icon="💡")

st.markdown("---")

st.info("Selecione uma funcionalidade no menu lateral ou através dos botões acima.")