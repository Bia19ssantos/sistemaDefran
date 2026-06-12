import streamlit as st
import pandas as pd
import os

import streamlit as st

# Logo na barra lateral
st.sidebar.image("navbar-logo.png", width=200)

# Cards coloridos
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""<div style="background-color:#007bff; color:white; padding:15px; border-radius:5px;">
    <b></b><br> </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div style="background-color:#ffc107; color:black; padding:15px; border-radius:5px;">
    <b></b><br> </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div style="background-color:#28a745; color:white; padding:15px; border-radius:5px;">
    <b></b><br> </div>""", unsafe_allow_html=True)
with col4:
    st.markdown("""<div style="background-color:#dc3545; color:white; padding:15px; border-radius:5px;">
    <b></b><br> </div>""", unsafe_allow_html=True)

st.markdown("---") # Linha divisória

# Configuração da página
st.set_page_config(page_title="Consultar Itens", layout="centered")

st.title("")
st.sidebar.header("Consultas")

# Função para carregar os dados
def carregar_dados():
    # Defina os nomes das colunas exatamente como no seu banco
    colunas = [
        'ref_prod', 'desc_prod', 'ncm', 'sap', 'ipi', 
        'tipo', 'valor_custo', 'carga_trabalho', 'comprimento', 'valor_venda'
    ]
    
    arquivos = {
        "Produtos Gunnebo": "prod_gunnebo.csv",
        "Produtos Crosby": "prod_crosby.csv",
        "Manilhas Crosby": "manilhas_crosby.csv"
    }
    
    dados = {}
    for nome, arquivo in arquivos.items():
        caminho_completo = f"dados/{arquivo}"
        
        if os.path.exists(caminho_completo):
            # Lemos informando que não tem cabeçalho (header=None) e passando nossa lista de colunas
            dados[nome] = pd.read_csv(
                caminho_completo, 
                sep=';', 
                encoding='latin1', 
                names=colunas, 
                header=None
            )
        else:
            st.warning(f"Arquivo {arquivo} não encontrado na pasta 'dados'!")
            
    return dados

# Carregar dados
dados_carregados = carregar_dados()

# Interface de seleção
if dados_carregados:
    selecao = st.sidebar.selectbox("Escolha a base:", list(dados_carregados.keys()))
    df = dados_carregados[selecao]

    # Campo de busca
    termo = st.text_input("Filtrar por referência (ref_prod):")
    
    if termo:
        # Filtra baseado na coluna 'ref_prod'
        df = df[df['ref_prod'].astype(str).str.contains(termo, case=False)]

    # Exibição da Tabela
    st.dataframe(df, use_container_width=True)

    # Exibição dos Detalhes (apenas se houver 1 resultado)
    st.subheader("Detalhes do Produto")
    
    if len(df) == 1:
        produto = df.iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Referência", value=str(produto['ref_prod']))
        with col2:
            # Formatando valores para 2 casas decimais
            custo = float(produto['valor_custo'])
            st.metric(label="Preço de Custo", value=f"R$ {custo:.2f}")
        with col3:
            venda = float(produto['valor_venda'])
            st.metric(label="Preço de Venda", value=f"R$ {venda:.2f}")
            
    elif len(df) > 1:
        st.info("Resultado com múltiplos itens. Filtre por uma referência específica para ver os preços detalhados.")
    else:
        st.write("Nenhum produto encontrado com este filtro.")
else:
    st.error("Nenhum arquivo CSV foi carregado. Verifique a pasta 'dados' no GitHub.")
