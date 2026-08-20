import streamlit as st
import pandas as pd
import os
import base64
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
    except Exception as e:
        st.warning(f"Usando arquivo local (Erro no Google: {e})")
        return pd.read_csv("dados/estoque_defran.csv", sep=',', encoding='latin1')

def carregar_dados():
    colunas_prod = [
        'ref_prod',
        'desc_prod',
        'ncm',
        'sap',
        'ipi',
        'tipo',
        'valor_custo',
        'carga_trabalho',
        'comprimento',
        'valor_venda'
    ]

    arquivos = {
        "Produtos Gunnebo": "prod_gunnebo.csv",
        "Produtos Crosby": "prod_crosby.csv",
        "Manilhas Crosby": "manilhas_crosby.csv"
    }

    dados = {}

    for nome, arquivo in arquivos.items():
        caminho = f"dados/{arquivo}"

        if os.path.exists(caminho):
            dados[nome] = pd.read_csv(
                caminho,
                sep=';',
                encoding='latin1',
                names=colunas_prod,
                header=0
            )

    dados["Estoque Defran"] = carregar_estoque_do_google()

    return dados

dados_carregados = carregar_dados()

# --- INTERFACE ---
aba1, aba2, aba3 = st.tabs(["Produtos", "Estoque Defran", "Carga de Trabalho Lingas"])

with aba1:
    selecao = st.selectbox(
        "Escolha a base:",
        ["Produtos Gunnebo", "Produtos Crosby", "Manilhas Crosby"]
    )

    if selecao in dados_carregados:
        df = dados_carregados[selecao]

        termo = st.text_input("Filtrar referência (Produtos):")

        if termo:
            df = df[
                df['ref_prod']
                .astype(str)
                .str.contains(termo, case=False, na=False)
            ]

        # =========================
        # PRODUTOS GUNNEBO
        # =========================
        if selecao == "Produtos Gunnebo":

            df_exibicao = df.rename(columns={
                'ref_prod': 'Referência Gunnebo',
                'desc_prod': 'Descrição do Produto',
                'ncm': 'NCM',
                'sap': 'Código SAP',
                'ipi': 'IPI',
                'tipo': 'Tipo',
                'valor_custo': 'Custo',
                'carga_trabalho': 'Carga de Trabalho',
                'comprimento': 'Comprimento',
                'valor_venda': 'Preço de Venda'
            })

        # =========================
        # CROSBY E MANILHAS
        # =========================
        else:

            df_exibicao = df.rename(columns={
                'ref_prod': 'Referência',
                'desc_prod': 'Descrição',
                'ncm': 'NCM',
                'sap': 'SAP',
                'ipi': 'IPI',
                'tipo': 'Tipo',
                'valor_custo': 'Valor de Custo',
                'valor_venda': 'Preço de Venda'
            })

            # Não exibir estas colunas no Crosby/Manilhas
            df_exibicao = df_exibicao.drop(
                columns=['carga_trabalho', 'comprimento'],
                errors='ignore'
            )

        st.dataframe(
            df_exibicao,
            use_container_width=True
        )
        
with aba2:
    st.header("Estoque Defran")
    
    termo_busca = st.text_input("🔍 Filtrar por código ou referência:", key="busca_estoque")
    df_est = dados_carregados["Estoque Defran"]
    
    if st.session_state.get("busca_estoque"):
        termo = st.session_state.busca_estoque
        df_est = df_est[
            df_est['codigo'].astype(str).str.contains(termo, case=False) | 
            df_est['ref_prod'].astype(str).str.contains(termo, case=False)
        ]

    event = st.dataframe(df_est, use_container_width=True, on_select="rerun", selection_mode="single-row")

    if "ultima_selecao" not in st.session_state:
        st.session_state.ultima_selecao = None

    if event.selection.rows:
        st.session_state.ultima_selecao = event.selection.rows[0]

    dados_padrao = {"id": "", "codigo": "", "ref_prod": "", "qtde": 0.0, "desc_prod": ""}
    if st.session_state.ultima_selecao is not None:
        try:
            linha = df_est.iloc[st.session_state.ultima_selecao]
            dados_padrao = linha.to_dict()
        except:
            st.session_state.ultima_selecao = None

    st.markdown("---")
    st.subheader("Atualizar ou Inserir Estoque")
    
    st.markdown("""
        <style>
        div.stFormSubmitButton > button {
            background-color: #28a745 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form(key="form_estoque", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        id_i = col1.text_input("Id", value=str(dados_padrao.get("id", "")))
        cod_i = col2.text_input("Codigo", value=str(dados_padrao.get("codigo", "")))
        ref_i = col3.text_input("Referencia", value=str(dados_padrao.get("ref_prod", "")))
        qtd_i = col4.number_input("Qtde", value=float(dados_padrao.get("qtde", 0)), step=0.01)
        desc_i = st.text_input("Descricao", value=str(dados_padrao.get("desc_prod", "")))
        
        submit = st.form_submit_button("Salvar Alteração")

    if submit:
        try:
            sheet = client.open("estoque_defran").sheet1
            cell = sheet.find(id_i) 
            if cell:
                sheet.update(f"A{cell.row}:E{cell.row}", [[id_i, cod_i, ref_i, desc_i, float(qtd_i)]])
                st.success(f"Item {id_i} atualizado!")
            else:
                sheet.append_row([id_i, cod_i, ref_i, desc_i, float(qtd_i)])
                st.success(f"Novo item {id_i} adicionado!")
            
            st.cache_data.clear()
            st.session_state.ultima_selecao = None
            if "busca_estoque" in st.session_state:
                del st.session_state["busca_estoque"]
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")


   with aba3:
    st.header("Carga de Trabalho - Lingas")
    
    caminho_pdf = "docs/cargaTrabalhoLingas.pdf"
    
    if os.path.exists(caminho_pdf):
        with open(caminho_pdf, "rb") as f:
            pdf_bytes = f.read()
            
        # Converte para base64 para abrir em nova aba de forma segura
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="text-decoration: none;"><button style="width: 100%; background-color: #007bff; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;">📄 Abrir PDF em Nova Aba</button></a>'
        
        st.markdown(href, unsafe_allow_html=True)
        st.write("") # Espaçamento
        
        # Mantém o botão de download caso o usuário queira baixar
        st.download_button(
            label="📥 Baixar PDF",
            data=pdf_bytes,
            file_name="cargaTrabalhoLingas.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.error(f"O arquivo PDF não foi encontrado em: {caminho_pdf}")
