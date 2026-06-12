import streamlit as st
import pandas as pd
import os

# Configuração inicial
st.set_page_config(page_title="Consultas Defran", layout="centered")

st.title("📊 Consultas Defran")
st.sidebar.header("Configurações")

# 1. Carregamento dos arquivos (coloque os CSVs na mesma pasta do script)
# Se estiverem no Drive, você pode baixar a pasta para o seu computador
def carregar_dados():
    arquivos = {
        "Produtos Gunnebo": "prod_gunnebo.csv",
        "Produtos Crosby": "prod_crosby.csv",
        "Manilhas Crosby": "manilhas_crosby.csv"
    }
    
    dados = {}
    for nome, arquivo in arquivos.items():
        if os.path.exists(arquivo):
            dados[nome] = pd.read_csv(arquivo)
        else:
            st.warning(f"Arquivo {arquivo} não encontrado!")
    return dados

dados_carregados = carregar_dados()

# 2. Seleção de qual planilha consultar
if dados_carregados:
    selecao = st.sidebar.selectbox("Escolha a base:", list(dados_carregados.keys()))
    df = dados_carregados[selecao]

    # 3. Campo de busca (filtro em tempo real)
    termo = st.text_input("Filtrar por referência ou nome...")
    
    if termo:
        # Filtra buscando em todas as colunas de texto
        mask = df.apply(lambda row: row.astype(str).str.contains(termo, case=False).any(), axis=1)
        df = df[mask]

    # 4. Exibição dos dados
    st.dataframe(df, use_container_width=True)
else:
    st.error("Nenhum arquivo CSV foi carregado. Verifique os nomes dos arquivos.")