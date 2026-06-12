import streamlit as st
import pandas as pd
import os

# 1. Configuração da página (DEVE SER O PRIMEIRO COMANDO)
st.set_page_config(page_title="Consultas Defran", layout="centered")

# 2. Sidebar e Logo
if os.path.exists("navbar-logo.png"):
    st.sidebar.image("navbar-logo.png", width=200)
st.sidebar.header("")

st.title("📊 Consultas Defran")

# --- FUNÇÃO DE CARREGAMENTO ---
def carregar_dados():
    colunas_prod = [
        'ref_prod', 'desc_prod', 'ncm', 'sap', 'ipi', 
        'tipo', 'valor_custo', 'carga_trabalho', 'comprimento', 'valor_venda'
    ]
    
    arquivos = {
        "Produtos Gunnebo": "prod_gunnebo.csv",
        "Produtos Crosby": "prod_crosby.csv",
        "Manilhas Crosby": "manilhas_crosby.csv"
    }
    
    dados = {}
    # Carrega arquivos de produtos (sem cabeçalho)
    for nome, arquivo in arquivos.items():
        caminho = f"dados/{arquivo}"
        if os.path.exists(caminho):
            dados[nome] = pd.read_csv(caminho, sep=';', encoding='latin1', names=colunas_prod, header=None)
    
    # Carrega o Estoque (com cabeçalho)
    caminho_est = "dados/estoque_defran.csv"
    if os.path.exists(caminho_est):
        dados["Estoque Defran"] = pd.read_csv(caminho_est, sep=',', encoding='latin1')
        
    return dados

dados_carregados = carregar_dados()

# --- ABA 1: CONSULTA DE PRODUTOS ---
aba1, aba2 = st.tabs(["Produtos", "Estoque Defran"])

with aba1:
    selecao = st.selectbox("Escolha a base:", ["Produtos Gunnebo", "Produtos Crosby", "Manilhas Crosby"])
    if selecao in dados_carregados:
        df = dados_carregados[selecao]
        termo = st.text_input("Filtrar referência (Produtos):")
        
        if termo:
            df = df[df['ref_prod'].astype(str).str.contains(termo, case=False)]
        
        st.dataframe(df, use_container_width=True)
        
        if len(df) == 1:
            prod = df.iloc[0]
            st.subheader("Detalhes do Produto")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ref", str(prod['ref_prod']))
            c2.metric("Custo", f"R$ {float(prod['valor_custo']):.2f}")
            c3.metric("Venda", f"R$ {float(prod['valor_venda']):.2f}")

# --- ABA 2: ESTOQUE DEFRAN ---
with aba2:
    if "Estoque Defran" in dados_carregados:
        df_est = dados_carregados["Estoque Defran"]
        busca = st.text_input("Buscar por código ou referência (Estoque):")
        if busca:
            df_est = df_est[df_est['codigo'].astype(str).str.contains(busca, case=False) | 
                            df_est['ref_prod'].astype(str).str.contains(busca, case=False)]
        st.dataframe(df_est, use_container_width=True)
    else:
        st.error("Arquivo 'estoque_defran.csv' não encontrado na pasta 'dados'!")
