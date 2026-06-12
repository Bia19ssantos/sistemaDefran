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

    # 1. Configuração da tabela com seleção
    event = st.dataframe(
        df_est, 
        use_container_width=True, 
        on_select="rerun", 
        selection_mode="single-row"
    )

    # 2. Guardar a seleção no session_state para não perder ao recarregar
    if "ultima_selecao" not in st.session_state:
        st.session_state.ultima_selecao = None

    if event.selection.rows:
        st.session_state.ultima_selecao = event.selection.rows[0]

    # 3. Definir dados padrão baseado no que está no session_state
    dados_padrao = {"id": "", "codigo": "", "ref_prod": "", "qtde": 0.0, "desc_prod": ""}
    if st.session_state.ultima_selecao is not None:
        try:
            linha = df_est.iloc[st.session_state.ultima_selecao]
            dados_padrao = linha.to_dict()
        except:
            pass

    st.markdown("---")
    st.subheader("Atualizar ou Inserir Estoque")
    
    # Adicionamos uma "key" dinâmica ao formulário para forçar a atualização dos campos
    key_form = f"form_{st.session_state.ultima_selecao}"
    
    with st.form(key=key_form, clear_on_submit=False):
        col1, col2, col3, col4 = st.columns(4)
        id_i = col1.text_input("Id", value=str(dados_padrao.get("id", "")))
        cod_i = col2.text_input("Codigo", value=str(dados_padrao.get("codigo", "")))
        ref_i = col3.text_input("Referencia", value=str(dados_padrao.get("ref_prod", "")))
        qtd_i = col4.number_input("Qtde", value=float(dados_padrao.get("qtde", 0)), step=0.01)
        desc_i = st.text_input("Descricao", value=str(dados_padrao.get("desc_prod", "")))
        
        submit = st.form_submit_button("Salvar Alteração")

    if submit:
        st.success(f"Dados do item {cod_i} prontos para salvar!")
        # AQUI VOCÊ PODE CHAMAR A FUNÇÃO DE SALVAR NO GOOGLE SHEETS
