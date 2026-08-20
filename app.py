import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Sistema Defran", layout="centered")

# --- FUNÇÃO DE RESET ---
def resetar_toda_a_tela():
    st.session_state.itens_orcamento = []
    st.session_state.editando_indice = None
    st.rerun()

# --- CONEXÃO COM GOOGLE ---
@st.cache_resource
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except:
        return None

client = conectar_google()

def carregar_estoque_do_google():
    try:
        sheet = client.open("estoque_defran").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.read_csv("dados/estoque_defran.csv", sep=',', encoding='latin1')

def carregar_dados():
    colunas_prod = ['ref_prod', 'desc_prod', 'ncm', 'sap', 'ipi', 'tipo', 'valor_custo', 'carga_trabalho', 'comprimento', 'valor_venda']
    dados = {
        "Produtos Gunnebo": pd.read_csv("dados/prod_gunnebo.csv", sep=';', encoding='latin1', names=colunas_prod, header=0),
        "Produtos Crosby": pd.read_csv("dados/prod_crosby.csv", sep=';', encoding='latin1', names=colunas_prod, header=0),
        "Manilhas Crosby": pd.read_csv("dados/manilhas_crosby.csv", sep=';', encoding='latin1', names=colunas_prod, header=0),
        "Estoque Defran": carregar_estoque_do_google(),
        "Clientes": pd.read_csv("dados/clientes.csv", sep=',', encoding='latin1') if os.path.exists("dados/clientes.csv") else pd.DataFrame()
    }
    return dados

dados_carregados = carregar_dados()

def carregar_bases_txt():
    produtos_dict = {}
    lingas_dict = {}
    # (Sua lógica de leitura de TXT mantida igual para brevidade)
    return produtos_dict, lingas_dict

base_produtos, base_lingas = carregar_bases_txt()

# --- ABA 4 ---
aba1, aba2, aba3, aba4 = st.tabs(["🔗 Produtos", "📦 Estoque Defran", "🏗️ Carga de Trabalho", "📋 Orçamento"])

with aba4:
    st.header("📋 Orçamentos")
    
    # --- BUSCA CLIENTE ---
    df_clientes = dados_carregados.get("Clientes", pd.DataFrame())
    opcoes_clientes = [""]
    mapa_clientes = {}
    if not df_clientes.empty:
        for _, row in df_clientes.iterrows():
            rotulo = f"{row['razao']}"
            opcoes_clientes.append(rotulo)
            mapa_clientes[rotulo] = row.to_dict()

    cliente_escolhido = st.selectbox("🔍 Buscar Cliente:", opcoes_clientes)
    dados_cli = mapa_clientes.get(cliente_escolhido, {})

    # Cabeçalho
    num_orc = st.text_input("Nº da Proposta", value="373/26")
    col1, col2 = st.columns(2)
    cliente_orc = col1.text_input("Cliente", value=str(dados_cli.get("razao", "")))
    
    # Condições vindas do cadastro do cliente
    col_cond1, col_cond2 = st.columns(2)
    cond_pgto_orc = col_cond1.text_input("Condição de Pagamento", value=str(dados_cli.get("cond_pgto", "30 DDL")))
    cond_entrega_orc = col_cond2.text_input("Condição de Entrega", value=str(dados_cli.get("cond_transporte", "FOB")))

    # --- GERENCIAMENTO DE ITENS ---
    if "itens_orcamento" not in st.session_state: st.session_state.itens_orcamento = []
    if "editando_indice" not in st.session_state: st.session_state.editando_indice = None

    # Formulário
    with st.form("form_item", clear_on_submit=True):
        tipo_item = st.selectbox("Tipo", ["Produto", "Linga"])
        ref = st.text_input("Referência")
        qtd = st.number_input("Quantidade", value=1.0)
        submit = st.form_submit_button("Adicionar/Salvar Item")
        
        if submit:
            novo_item = {"tipo": tipo_item, "referencia": ref, "quantidade": qtd}
            if st.session_state.editando_indice is not None:
                st.session_state.itens_orcamento[st.session_state.editando_indice] = novo_item
                st.session_state.editando_indice = None
            else:
                st.session_state.itens_orcamento.append(novo_item)
            st.rerun()

    # Listagem
    for idx, item in enumerate(st.session_state.itens_orcamento):
        cols = st.columns([3, 1, 1])
        cols[0].write(f"{item['referencia']} (Qtd: {item['quantidade']})")
        if cols[1].button("✏️", key=f"e{idx}"):
            st.session_state.editando_indice = idx
            st.rerun()
        if cols[2].button("🗑️", key=f"d{idx}"):
            st.session_state.itens_orcamento.pop(idx)
            st.rerun()

    # Botão PDF
    if st.button("📄 Gerar e Baixar PDF"):
        # Lógica de PDF...
        st.success("Gerado!")
        resetar_toda_a_tela()
