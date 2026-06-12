import streamlit as st
import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Consultas Defran", layout="centered")

# --- CONEXÃO COM GOOGLE ---
@st.cache_resource
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

client = conectar_google()

def carregar_estoque_do_google():
    try:
        sheet = client.open("estoque_defran").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        st.warning("Usando arquivo local (erro ao conectar no Google).")
        return pd.read_csv("dados/estoque_defran.csv", sep=',', encoding='latin1')

# --- CARREGAMENTO GERAL ---
def carregar_dados():
    colunas_prod = ['ref_prod', 'desc_prod', 'ncm', 'sap', 'ipi', 'tipo', 'valor_custo', 'carga_trabalho', 'comprimento', 'valor_venda']
    arquivos = {"Produtos Gunnebo": "prod_gunnebo.csv", "Produtos Crosby": "prod_crosby.csv", "Manilhas Crosby": "manilhas_crosby.csv"}
    dados = {}
    for nome, arquivo in arquivos.items():
        caminho = f"dados/{arquivo}"
        if os.path.exists(caminho):
            dados[nome] = pd.read_csv(caminho, sep=';', encoding='latin1', names=colunas_prod, header=None)
    dados["Estoque Defran"] = carregar_estoque_do_google()
    return dados

dados_carregados = carregar_dados()

# --- INTERFACE ---
aba1, aba2 = st.tabs(["Produtos", "Estoque Defran"])

with aba1:
    selecao = st.selectbox("Escolha a base:", ["Produtos Gunnebo", "Produtos Crosby", "Manilhas Crosby"])
    if selecao in dados_carregados:
        df = dados_carregados[selecao]
        termo = st.text_input("Filtrar referência (Produtos):")
        if termo: df = df[df['ref_prod'].astype(str).str.contains(termo, case=False)]
        st.dataframe(df, use_container_width=True)

with aba2:
    st.header("Estoque Defran")
    df_est = dados_carregados["Estoque Defran"]
    st.dataframe(df_est, use_container_width=True)
    
    # FORMULÁRIO DENTRO DA ABA
    st.markdown("---")
    st.subheader("Atualizar Estoque")
    with st.form("form_estoque", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        id_i = col1.text_input("Id")
        cod_i = col2.text_input("Codigo")
        ref_i = col3.text_input("Referencia")
        qtd_i = col4.number_input("Qtde", step=0.01)
        desc_i = st.text_input("Descricao")
        submit = st.form_submit_button("Salvar")

    if submit:
        try:
            sheet = client.open("estoque_defran").sheet1
            sheet.append_row([id_i, cod_i, ref_i, desc_i, qtd_i])
            st.success("Salvo com sucesso! Recarregue a página para ver a atualização.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
