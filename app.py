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
from datetime import datetime

st.set_page_config(page_title="Sistema Defran", layout="centered")

# --- CONTROLE DE SESSÃO E LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = ""
if "etapa_boas_vindas" not in st.session_state:
    st.session_state.etapa_boas_vindas = False

# 1. TELA DE LOGIN
if not st.session_state.autenticado:
    _, col_centro, _ = st.columns([1, 1.5, 1])
    
    with col_centro:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("navbar-logo.jpg"):
            st.image("navbar-logo.jpg", width=300)
        elif os.path.exists("navbar-logo.png"):
            st.image("navbar-logo.png", width=300)
        elif os.path.exists("docs/logoDefran1.png"):
            st.image("docs/logoDefran1.png", width=300)
            
        st.markdown("### Acesso ao Sistema Defran")
        
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_entrar:
                usuarios_validos = {
                    "beatriz": "626134",
                    "deise": "626134",
                    "roberto": "626134"
                }
                
                usuario_limpo = usuario_input.strip().lower()
                
                if usuario_limpo in usuarios_validos and usuarios_validos[usuario_limpo] == senha_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_logado = usuario_input.strip().capitalize()
                    st.session_state.etapa_boas_vindas = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
    st.stop()

# 2. TELA DE POP-UP DE BOAS-VINDAS
if st.session_state.get("etapa_boas_vindas"):
    _, col_centro2, _ = st.columns([1, 2, 1])
    
    with col_centro2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("navbar-logo.jpg"):
            st.image("navbar-logo.jpg", width=350)
        elif os.path.exists("navbar-logo.png"):
            st.image("navbar-logo.png", width=350)
        elif os.path.exists("docs/logoDefran1.png"):
            st.image("docs/logoDefran1.png", width=350)
            
        st.markdown(f"### Olá, {st.session_state.usuario_logado}! Bem-vindo(a) ao Sistema Defran")
        st.markdown("Gerenciamento de Produtos, Estoque e Propostas Comerciais.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Ir ao Menu Principal", type="primary", use_container_width=True):
            st.session_state.etapa_boas_vindas = False
            st.rerun()
            
    st.stop()
    
if os.path.exists("navbar-logo.jpg"):
    st.image("navbar-logo.jpg", width=300)
elif os.path.exists("navbar-logo.png"):
    st.image("navbar-logo.png", width=300)

st.markdown("---")
@st.cache_resource

def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    except Exception:
        return None

client = conectar_google()

def carregar_estoque_do_google():
    try:
        sheet = conectar_gspread()
        dados_brutos = sheet.get_all_values()
        if len(dados_brutos) > 1:
            cabecalho = [str(c).strip().lower() for c in dados_brutos[0]]
            linhas = dados_brutos[1:]
            df = pd.DataFrame(linhas, columns=cabecalho)
            return df
        else:
            return pd.DataFrame()
    except Exception as ex:
        st.error(f"Erro ao carregar o estoque do Google Sheets: {ex}")
        return pd.DataFrame()

def carregar_dados():
    cols_gunnebo = ['ref_prod', 'desc_prod', 'ncm', 'sap', 'ipi', 'tipo', 'valor_custo', 'comprimento', 'valor_venda', 'preco_linga']
    cols_crosby = ['ref_prod', 'desc_prod', 'ncm', 'sap', 'ipi', 'tipo', 'valor_custo', 'carga_trabalho', 'comprimento', 'valor_venda']
    
    arquivos = {
        "Produtos Gunnebo": ("prod_gunnebo.csv", cols_gunnebo),
        "Produtos Crosby": ("prod_crosby.csv", cols_crosby),
        "Manilhas Crosby": ("manilhas_crosby.csv", cols_crosby)
    }
    
    dados_carregados = {}
    
    for nome, (arquivo, colunas) in arquivos.items():
        caminho = f"dados/{arquivo}"
        if os.path.exists(caminho):
            try:
                dados_carregados[nome] = pd.read_csv(caminho, sep=';', names=colunas, encoding='latin1', header=0)
            except Exception as e:
                dados_carregados[nome] = pd.DataFrame()
        else:
            dados_carregados[nome] = pd.DataFrame()
            
    dados_carregados["Estoque Defran"] = carregar_estoque_do_google()
     
    caminho_clientes = "dados/clientes.csv"
    if os.path.exists(caminho_clientes):
        dados_carregados["Clientes"] = pd.read_csv(caminho_clientes, sep=',', encoding='latin1')
    else:
        dados_carregados["Clientes"] = pd.DataFrame()
        
    return dados_carregados

dados_carregados = carregar_dados()

# --- Aba Principal ---
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "🔗 Produtos", 
    "📦 Estoque Defran", 
    "🏗️ Carga de Trabalho",
    "📋 Orçamento",
    "📥📤 Notas Fiscais"
])

# --- ABA 1: PRODUTOS ---
with aba1:
    st.header("📦 Consulta de Produtos")
    
    selecao_aba1 = st.selectbox(
        "Escolha a base:",
        ["Produtos Gunnebo", "Produtos Crosby", "Manilhas Crosby"],
        key="select_base_aba1"
    )

    if selecao_aba1 in dados_carregados and not dados_carregados[selecao_aba1].empty:
        df_aba1 = dados_carregados[selecao_aba1].copy()

        termo_aba1 = st.text_input("Filtrar por Referência ou Código SAP:", key=f"filtro_aba1_{selecao_aba1}")

        if termo_aba1:
            filtro_ref = df_aba1['ref_prod'].astype(str).str.contains(termo_aba1, case=False, na=False)
            filtro_sap = df_aba1['sap'].astype(str).str.contains(termo_aba1, case=False, na=False)
            df_aba1 = df_aba1[filtro_ref | filtro_sap]

        def formatar_moeda(val):
            try:
                num = float(val)
                return f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return val

        if selecao_aba1 == "Produtos Gunnebo":
            for col in ['valor_custo', 'valor_venda', 'preco_linga']:
                if col in df_aba1.columns:
                    df_aba1[col] = df_aba1[col].apply(formatar_moeda)

            df_exibicao_aba1 = df_aba1.rename(columns={
                'sap': 'SAP',
                'ref_prod': 'Referência',
                'ipi': 'IPI',
                'comprimento': 'Comprimento',
                'valor_custo': 'Valor Custo',
                'valor_venda': 'Valor Venda',
                'preco_linga': 'Valor Linga'
            })
            colunas_desejadas = ['SAP', 'Referência', 'IPI', 'Comprimento', 'Valor Custo', 'Valor Venda', 'Valor Linga']
        else:
            for col in ['valor_custo', 'valor_venda']:
                if col in df_aba1.columns:
                    df_aba1[col] = df_aba1[col].apply(formatar_moeda)

            df_exibicao_aba1 = df_aba1.rename(columns={
                'sap': 'SAP',
                'ref_prod': 'Referência',
                'ncm': 'NCM',
                'ipi': 'IPI',
                'valor_custo': 'Valor Custo',
                'valor_venda': 'Valor Venda'
            })
            colunas_desejadas = ['SAP', 'Referência', 'NCM', 'IPI', 'Valor Custo', 'Valor Venda']

        colunas_existentes = [c for c in colunas_desejadas if c in df_exibicao_aba1.columns]
        df_exibicao_aba1 = df_exibicao_aba1[colunas_existentes]

        st.dataframe(df_exibicao_aba1, use_container_width=True)
    else:
        st.warning(f"A base '{selecao_aba1}' não foi encontrada ou está vazia.")


# --- ABA 2: ESTOQUE DEFRAN ---
with aba2:
    st.header("Estoque Defran")
    termo_busca = st.text_input("🔍 Filtrar por código ou referência:", key="busca_estoque")
    df_est = dados_carregados["Estoque Defran"]
    if st.session_state.get("busca_estoque") and not df_est.empty:
        termo = st.session_state.busca_estoque
        df_est = df_est[df_est['codigo'].astype(str).str.contains(termo, case=False) | df_est['ref_prod'].astype(str).str.contains(termo, case=False)]
    event = st.dataframe(df_est, use_container_width=True, on_select="rerun", selection_mode="single-row")

    if "ultima_selecao" not in st.session_state:
        st.session_state.ultima_selecao = None
    if event and event.selection.rows:
        st.session_state.ultima_selecao = event.selection.rows[0]

    dados_padrao = {"id": "", "codigo": "", "ref_prod": "", "qtde": 0.0, "desc_prod": ""}
    if st.session_state.ultima_selecao is not None and not df_est.empty:
        try:
            dados_padrao = df_est.iloc[st.session_state.ultima_selecao].to_dict()
        except:
            st.session_state.ultima_selecao = None

    with st.form(key="form_estoque", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        id_i = col1.text_input("Id", value=str(dados_padrao.get("id", "")))
        cod_i = col2.text_input("Codigo", value=str(dados_padrao.get("codigo", "")))
        ref_i = col3.text_input("Referencia", value=str(dados_padrao.get("ref_prod", "")))
        qtd_i = col4.number_input("Qtde", value=float(dados_padrao.get("qtde", 0)), step=0.01)
        desc_i = st.text_input("Descricao", value=str(dados_padrao.get("desc_prod", "")))
        submit = st.form_submit_button("Salvar Alteração")

    if submit and client:
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
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- ABA 3: CARGA DE TRABALHO LINGAS ---
with aba3:
    st.header("📊 Carga de Trabalho - Lingas")
    caminho_pdf = "docs/cargas_lingas.pdf"
    
    if os.path.exists(caminho_pdf):
        st.info("O visualizador integrado pode ser bloqueado por alguns navegadores. Utilize o botão abaixo para baixar ou visualizar o documento completo com facilidade.")
        with open(caminho_pdf, "rb") as f:
            st.download_button(
                label="📥 Baixar / Visualizar PDF de Carga de Trabalho",
                data=f,
                file_name="cargas_lingas.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        st.markdown("---")
        with open(caminho_pdf, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<object data="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="100%" height="700px"><p>Seu navegador não suporta a visualização direta de PDFs.</p></object>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error(f"O arquivo PDF não foi encontrado no caminho: {caminho_pdf}.")

# --- ABA 4: CADASTRO DE ORÇAMENTO ---
with aba4:
    # --- ESTILO CSS PERSONALIZADO PARA OS BOTÕES ---
    st.markdown("""
        <style>
        /* Botão Primário (Adicionar / Salvar Item) - Azul Suave */
        div.stButton > button[kind="primary"], 
        div.stFormSubmitButton > button {
            background-color: #0066cc !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: 500 !important;
        }
        div.stButton > button[kind="primary"]:hover, 
        div.stFormSubmitButton > button:hover {
            background-color: #0052a3 !important;
        }

        /* Botão de Download (Gerar PDF) - Verde Suave */
        div.stDownloadButton > button {
            background-color: #28a745 !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: 500 !important;
        }
        div.stDownloadButton > button:hover {
            background-color: #218838 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("📋 Orçamentos")
    
    df_clientes = dados_carregados.get("Clientes", pd.DataFrame())
    
    opcoes_clientes = [""]
    mapa_clientes = {}
    if not df_clientes.empty:
        for _, row in df_clientes.iterrows():
            rotulo = f"{row.get('razao', '')} | Contato: {row.get('contato', '')}"
            opcoes_clientes.append(rotulo)
            mapa_clientes[rotulo] = row.to_dict()

    cliente_escolhido = st.selectbox("🔍 Buscar Cliente (Digite as primeiras letras da Razão Social ou do Contato):", opcoes_clientes)
    
    dados_cli = {}
    if cliente_escolhido and cliente_escolhido in mapa_clientes:
        dados_cli = mapa_clientes[cliente_escolhido]

    col_c1, col_c2, col_c3 = st.columns(3)
    num_orc = col_c1.text_input("Nº da Proposta", value="")
    
    meses_pt = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 
        5: "maio", 6: "junho", 7: "julho", 8: "agosto", 
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    agora = datetime.now()
    data_atual_formatada = f"{agora.day} de {meses_pt[agora.month]} de {agora.year}"
    data_orc = col_c2.text_input("Data", value=data_atual_formatada) 
    cliente_orc = col_c3.text_input("Cliente", value=str(dados_cli.get("razao", "")) if cliente_escolhido else "")
  
    col_c4, col_c5, col_c6 = st.columns(3)
    cidade_orc = col_c4.text_input("Cidade", value=str(dados_cli.get("cidade", "")) if cliente_escolhido else "")
    estado_orc = col_c5.text_input("Estado", value=str(dados_cli.get("estado", "")) if cliente_escolhido else "")
    tel_orc = col_c6.text_input("Telefone", value=str(dados_cli.get("telefone", "")) if cliente_escolhido else "")

    col_c7, col_c8 = st.columns(2)
    contato_orc = col_c7.text_input("Contato", value=str(dados_cli.get("contato", "")) if cliente_escolhido else "")
    email_orc = col_c8.text_input("E-mail", value=str(dados_cli.get("email", "")) if cliente_escolhido else "")
    vendedor_orc = st.text_input("Vendedor(a)", value="")

    col_cond1, col_cond2 = st.columns(2)
    cond_pgto_orc = col_cond1.text_input("Condição de Pagamento", value=str(dados_cli.get("cond_pgto", "")) if cliente_escolhido else "")
    cond_entrega_orc = col_cond2.text_input("Condição de Entrega", value=str(dados_cli.get("cond_transporte", "")) if cliente_escolhido else "")

    st.markdown("---")
    st.subheader("Adicionar ou Editar Itens na Proposta")
    
    if "itens_orcamento" not in st.session_state:
        st.session_state.itens_orcamento = []
    if "editando_indice" not in st.session_state:
        st.session_state.editando_indice = None

    if "limpar_campos_item" not in st.session_state:
        st.session_state.limpar_campos_item = False

    if st.session_state.limpar_campos_item:
        st.session_state["tipo_item_orcamento"] = "Produto"
        st.session_state["busca_manual_input"] = ""
        st.session_state["ref_linga_orc"] = ""
        st.session_state.limpar_campos_item = False

    item_editando = {}
    if st.session_state.editando_indice is not None and st.session_state.editando_indice < len(st.session_state.itens_orcamento):
        item_editando = st.session_state.itens_orcamento[st.session_state.editando_indice]
    
    tipos_disponiveis = ["Produto", "Linga"]
    tipo_atual = item_editando.get("tipo", "Produto")
    
    col_t1, col_t2 = st.columns(2)
    tipo_item = col_t1.selectbox(
        "Tipo de Item", 
        tipos_disponiveis, 
        index=tipos_disponiveis.index(tipo_atual) if tipo_atual in tipos_disponiveis else 0,
        key="tipo_item_orcamento"
    )

    base_selecionada = base_produtos if tipo_item == "Produto" else base_lingas

    dados_encontrados = {}
    busca_manual = ""

    if tipo_item == "Produto":
        busca_manual = col_t2.text_input("Digite o Código SAP ou Referência e aperte Enter:", key="busca_manual_input")
        if busca_manual:
            if busca_manual in base_selecionada:
                dados_encontrados = base_selecionada.get(busca_manual, {})
            else:
                for chave in base_selecionada.keys():
                    if busca_manual.lower() in chave.lower():
                        dados_encontrados = base_selecionada[chave]
                        break
            if not dados_encontrados:
                st.warning("Produto não encontrado no arquivo TXT. Verifique o código digitado.")
    else:
        ref_linga_digitada = col_t2.selectbox(
            "Buscar Referência de Linga:", 
            [""] + list(base_selecionada.keys()), 
            key="ref_linga_orc"
        )
        if ref_linga_digitada and ref_linga_digitada in base_selecionada:
            dados_encontrados = base_selecionada.get(ref_linga_digitada, {})
            busca_manual = ref_linga_digitada

    preco_sugerido_planilha = 0.0
    ref_ou_sap_alvo = dados_encontrados.get("referencia", "") or dados_encontrados.get("sap", "") or busca_manual

    if ref_ou_sap_alvo and "Produtos Gunnebo" in dados_carregados:
        df_gun = dados_carregados["Produtos Gunnebo"]
        if not df_gun.empty:
            match = df_gun[
                df_gun['ref_prod'].astype(str).str.contains(ref_ou_sap_alvo, case=False, na=False) |
                df_gun['sap'].astype(str).str.contains(ref_ou_sap_alvo, case=False, na=False)
            ]
            if not match.empty:
                try:
                    preco_sugerido_planilha = float(match.iloc[0]['valor_venda'])
                except:
                    pass

    if st.session_state.editando_indice is not None:
        fonte_dados = item_editando
    else:
        fonte_dados = dados_encontrados
        if preco_sugerido_planilha > 0 and not fonte_dados.get("unitario"):
            fonte_dados["unitario"] = preco_sugerido_planilha

    with st.form("form_item_orc", clear_on_submit=True):
        if st.session_state.editando_indice is not None:
            st.info(f"Editando o Item #{st.session_state.editando_indice + 1}")

        val_ref = ref_ou_sap_alvo if ref_ou_sap_alvo else fonte_dados.get("referencia", "")
        item_ref = st.text_input("Referência / Código Exato", value=val_ref)

        col_i1, col_i2, col_i3 = st.columns(3)
        item_qtd = col_i1.number_input("Quantidade / Metragem", min_value=0.01, 
                                       value=float(fonte_dados.get("quantidade", 1.00)), step=0.01)
        
        unidades_disponiveis = ["PÇ", "M"]
        unidade_atual = fonte_dados.get("unidade", "PÇ")
        idx_unidade = unidades_disponiveis.index(unidade_atual) if unidade_atual in unidades_disponiveis else 0
        item_unidade = col_i2.selectbox("Unidade", unidades_disponiveis, index=idx_unidade)
        
        val_inicial_unit = float(fonte_dados.get("unitario", 0.0))
        if val_inicial_unit == 0.0 and preco_sugerido_planilha > 0:
            val_inicial_unit = preco_sugerido_planilha
            
        item_val = col_i3.number_input("Valor Unitário (R$)", min_value=0.0, value=val_inicial_unit, step=0.10)
        
        item_desc = st.text_area("Descrição Completa", value=fonte_dados.get("descricao", ""))
        
        col_extra1, col_extra2, col_extra3, col_extra4 = st.columns(4)
        item_prazo = col_extra1.text_input("Prazo de Entrega", value=fonte_dados.get("prazo", "07 dias"))
        item_ncm = col_extra2.text_input("NCM", value=fonte_dados.get("ncm", ""))
        item_ipi = col_extra3.text_input("IPI", value=fonte_dados.get("ipi", "Incluso"))
        item_fator = col_extra4.text_input("Fator de Seg.", value=fonte_dados.get("fator", "4:1"))
        
        texto_botao = "Salvar Alteração do Item" if st.session_state.editando_indice is not None else "Adicionar Item na Proposta"
        add_item_btn = st.form_submit_button(texto_botao)
        
        if add_item_btn and item_ref:
            novo_dado_item = {
                "tipo": tipo_item,
                "referencia": item_ref,
                "descricao": item_desc,
                "quantidade": item_qtd,
                "unidade": item_unidade,
                "unitario": item_val,
                "prazo": item_prazo,
                "ncm": item_ncm,
                "ipi": item_ipi,
                "fator": item_fator,
                "total": item_qtd * item_val
            }
            
            if st.session_state.editando_indice is not None:
                st.session_state.itens_orcamento[st.session_state.editando_indice] = novo_dado_item
                st.session_state.editando_indice = None
                st.success("Item atualizado com sucesso!")
            else:
                st.session_state.itens_orcamento.append(novo_dado_item)
                st.success("Item adicionado com sucesso!")
            
            st.session_state.limpar_campos_item = True
            st.rerun()

    if st.session_state.editando_indice is not None:
        if st.button("❌ Cancelar Edição"):
            st.session_state.editando_indice = None
            st.rerun()

    if st.session_state.itens_orcamento:
        st.write("### Itens Na Proposta:")
        
        for idx, item in enumerate(st.session_state.itens_orcamento):
            col_res1, col_res2, col_res3, col_res4, col_res5, col_res6 = st.columns([1, 2, 2, 2, 1, 1])
            col_res1.write(f"**#{idx+1}**")
            col_res2.write(f"{item['tipo']}")
            col_res3.write(f"{item['referencia']}")
            col_res4.write(f"{item['quantidade']:.2f} {item['unidade']} - R$ {item['total']:.2f}")
            
            if col_res5.button("✏️ Editar", key=f"edit_{idx}"):
                st.session_state.editando_indice = idx
                st.rerun()
                
            if col_res6.button("🗑️ Excluir", key=f"del_{idx}"):
                st.session_state.itens_orcamento.pop(idx)
                if st.session_state.editando_indice == idx:
                    st.session_state.editando_indice = None
                st.rerun()

        if st.button("🗑️ Limpar Todos os Itens"):
            st.session_state.itens_orcamento = []
            st.session_state.editando_indice = None
            st.rerun()
        
        def gerar_pdf_defran(num, data, cliente, cidade, estado, tel, contato, email, vendedor, cond_pgto, cond_entrega, itens):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            elementos = []
            styles = getSampleStyleSheet()
            
            estilo_empresa = ParagraphStyle('Empresa', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#333333"))
            estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading2'], fontSize=12, leading=14, textColor=colors.HexColor("#0056b3"), alignment=1)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#222222"))
            estilo_bold = ParagraphStyle('Bold', parent=estilo_texto, fontName='Helvetica-Bold')
            
            caminho_logo_esq = "docs/logoDefran1.png"
            caminho_logo_dir = "docs/KitoCrosbyGunn.png"
            
            img_esquerda = None
            if os.path.exists(caminho_logo_esq):
                img_esquerda = Image(caminho_logo_esq, width=150, height=52)
            
            img_direita = None
            if os.path.exists(caminho_logo_dir):
                img_direita = Image(caminho_logo_dir, width=130, height=48)

            header_table_data = [
                [img_esquerda or Paragraph("<b>DEFRAN</b>", estilo_bold), img_direita or ""]
            ]
            t_header = Table(header_table_data, colWidths=[300, 240])
            t_header.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            elementos.append(t_header)
            
            elementos.append(Paragraph("Av. Getúlio Vargas, 966 Bambu/Porto Feliz-SP / CEP: 18540-380", estilo_empresa))
            elementos.append(Paragraph("CNPJ: 66.521.337/0001-52 / IE: 554.109.111.113", estilo_empresa))
            elementos.append(Spacer(1, 8))
            
            elementos.append(Paragraph("<b>PROPOSTA COMERCIAL</b>", estilo_titulo))
            elementos.append(Spacer(1, 8))
            
            info_topo = [
                [Paragraph(f"<b>PROPOSTA N°:</b> {num}", estilo_texto), Paragraph(f"<b>DATA:</b> {data}", estilo_texto)],
                [Paragraph(f"<b>VENDEDOR(A):</b> {vendedor}", estilo_texto), Paragraph("", estilo_texto)]
            ]
            t_topo = Table(info_topo, colWidths=[270, 270])
            t_topo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#e9ecef")),
                ('PADDING', (0,0), (-1,-1), 5),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#adb5bd")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elementos.append(t_topo)
            elementos.append(Spacer(1, 6))

            info_dados = [
                [Paragraph(f"<b>CLIENTE:</b> {cliente}", estilo_texto), Paragraph(f"<b>CONTATO:</b> {contato}", estilo_texto)],
                [Paragraph(f"<b>CIDADE:</b> {cidade} - {estado}", estilo_texto), Paragraph(f"<b>E-MAIL:</b> {email}", estilo_texto)],
                [Paragraph(f"<b>TEL:</b> {tel}", estilo_texto), Paragraph("", estilo_texto)]
            ]
            t_info = Table(info_dados, colWidths=[270, 270])
            t_info.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f9fa")),
                ('PADDING', (0,0), (-1,-1), 5),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elementos.append(t_info)
            elementos.append(Spacer(1, 10))
            
            elementos.append(Paragraph("Conforme Vossa solicitação, enviamos abaixo preço e demais condições de fornecimento para o(s) item(ns) abaixo:", estilo_texto))
            elementos.append(Spacer(1, 10))
            
            for idx, item in enumerate(itens, 1):
                item_dados = [
                    [Paragraph(f"<b>Item: {idx:02d}</b>", estilo_bold), Paragraph(f"<b>Quantidade:</b> {item['quantidade']:.2f} {item['unidade']}", estilo_bold)],
                    [Paragraph(f"<b>Referência:</b> {item['referencia']}", estilo_texto), Paragraph(f"<b>Preço Unit.:</b> R$ {item['unitario']:.2f}", estilo_bold)],
                    [Paragraph(f"<b>Descrição:</b> {item['descricao']}", estilo_texto), Paragraph("", estilo_texto)],
                    [Paragraph(f"<b>Prazo de Entrega:</b> {item['prazo']}", estilo_texto), Paragraph(f"<b>NCM:</b> {item['ncm']}", estilo_texto)],
                    [Paragraph("<b>ICMS:</b> Incluso (ST)", estilo_texto), Paragraph(f"<b>IPI:</b> {item['ipi']}", estilo_texto)],
                    [Paragraph(f"<b>Fator de Segurança:</b> {item['fator']}", estilo_texto), Paragraph(f"<b>Total do Item:</b> R$ {item['total']:.2f}", estilo_bold)]
                ]
                t_item = Table(item_dados, colWidths=[340, 200])
                t_item.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ffffff")),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0056b3")),
                    ('PADDING', (0,0), (-1,-1), 4),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                elementos.append(t_item)
                elementos.append(Spacer(1, 8))
                
            cond_dados = [
                [Paragraph("<b>\"TODOS OS IMPOSTOS INCLUSOS\"</b>", estilo_bold)],
                [Paragraph("<b>\"FORNECIDO COM CERTIFICADO DE QUALIDADE\"</b>", estilo_bold)],
                [Paragraph("<b>CONDIÇÕES COMERCIAIS:</b>", estilo_bold)],
                [Paragraph(f"• <b>Condição de Pagamento:</b> {cond_pgto}", estilo_texto)],
                [Paragraph(f"• <b>Condição de Entrega:</b> {cond_entrega}", estilo_texto)],
                [Paragraph("• <b>Validade da Proposta:</b> 10 dias (material sujeito à venda sem prévio aviso)", estilo_texto)],
                [Paragraph("<br/><b>Roberto Versiani</b><br/>Departamento de Vendas<br/>Tel. (15)3262-4134 - Cel. (15)98114-7575<br/>E. Mail: defran@defran.com.br", estilo_texto)]
            ]
            t_cond = Table(cond_dados, colWidths=[540])
            t_cond.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f3f5")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
            ]))
            elementos.append(t_cond)
            
            doc.build(elementos)
            buffer.seek(0)
            return buffer

        def limpar_tela_pos_pdf():
            st.session_state.itens_orcamento = []
            st.session_state.editando_indice = None

        pdf_buffer = gerar_pdf_defran(
            num_orc, data_orc, cliente_orc, 
            cidade_orc, estado_orc, tel_orc, contato_orc, 
            email_orc, vendedor_orc, cond_pgto_orc, cond_entrega_orc, st.session_state.itens_orcamento
        )
        
        primeira_palavra_cliente = cliente_orc.strip().split()[0] if cliente_orc else "CLIENTE"
        num_limpo = num_orc.split('/')[0] if '/' in num_orc else num_orc
        ano_atual = "26"
        nome_sugerido = f"ORC {num_limpo}/{ano_atual} - {primeira_palavra_cliente} - {contato_orc}.pdf"

        st.download_button(
            label="📥 Baixar PDF do Orçamento Defran",
            data=pdf_buffer,
            file_name=nome_sugerido,
            mime="application/pdf",
            use_container_width=True,
            on_click=limpar_tela_pos_pdf
        )


# --- ABA 5: NOTAS FISCAIS (ATUALIZAÇÃO DE ESTOQUE VIA GOOGLE SHEETS) ---
with aba5:
    st.header("📥📤 Gestão de Estoque via NF-e (Google Sheets)")
    st.write("Faça o upload do XML da Nota Fiscal para atualizar o estoque na nuvem")

    arquivo_xml_unico = st.file_uploader("Selecione o arquivo XML da NF-e", type=["xml"], key="upload_xml_sheets")
    
    if arquivo_xml_unico:
        try:
            tree = ET.parse(arquivo_xml_unico)
            root = tree.getroot()
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            infNFe = root.find('.//nfe:infNFe', ns)
            nNF, xNome = "", ""
            if infNFe is not None:
                ide = infNFe.find('nfe:ide', ns)
                if ide is not None:
                    nNF = ide.findtext('nfe:nNF', default='', namespaces=ns)
                emit = infNFe.find('nfe:emit', ns)
                if emit is not None:
                    xNome = emit.findtext('nfe:xNome', default='', namespaces=ns)
            
            st.info(f"**Nota Fiscal Nº:** {nNF} | **Emitente:** {xNome}")
            
            det_itens = root.findall('.//nfe:det', ns)
            produtos_nota = []
            
            for det in det_itens:
                prod = det.find('nfe:prod', ns)
                if prod is not None:
                    c_prod = prod.findtext('nfe:cProd', default='', namespaces=ns)
                    x_prod = prod.findtext('nfe:xProd', default='', namespaces=ns)
                    q_com = float(prod.findtext('nfe:qCom', default='0', namespaces=ns))
                    
                    produtos_nota.append({
                        "Código": str(c_prod).strip(),
                        "Descrição": x_prod,
                        "Quantidade": q_com
                    })
            
            if produtos_nota:
                df_produtos_nf = pd.DataFrame(produtos_nota)
                st.subheader("Produtos Constantes na Nota Fiscal:")
                st.dataframe(df_produtos_nf, use_container_width=True)
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)

                if col_btn1.button("📥 Dar Entrada no Estoque (Google Sheets)", use_container_width=True):
                    try:
                        sheet = conectar_gspread()
                        df_estoque = carregar_estoque_do_google()
                        
                        sucesso = True
                        for item in produtos_nota:
                            cod_nf = item["Código"]
                            qtd_nf = item["Quantidade"]
                            
                            if not df_estoque.empty and 'codigo' in df_estoque.columns:
                                mask = df_estoque['codigo'].astype(str).str.strip() == cod_nf
                                
                                if mask.any():
                                    idx_pandas = df_estoque[mask].index[0]
                                    row_number = idx_pandas + 2 
                                    
                                    try:
                                        qtd_atual = float(df_estoque.loc[idx_pandas, 'qtde'])
                                    except:
                                        qtd_atual = 0.0
                                        
                                    nova_qtd = qtd_atual + qtd_nf
                                    df_estoque.loc[idx_pandas, 'qtde'] = nova_qtd
                                    
                                    colunas_sheet = [str(c).strip().lower() for c in sheet.row_values(1)]
                                    if 'qtde' in colunas_sheet:
                                        col_index = colunas_sheet.index('qtde') + 1
                                        sheet.update_cell(row_number, col_index, nova_qtd)
                                else:
                                    st.warning(f"Produto {cod_nf} não encontrado no Google Sheets.")
                                    sucesso = False
                            else:
                                st.warning("A planilha do Google Sheets está vazia ou sem a coluna 'codigo'.")
                                sucesso = False
                                
                        if sucesso:
                            st.success("Entrada registrada e salva no Google Sheets com sucesso!")
                            st.cache_data.clear()
                    except Exception as err:
                        st.error(f"Erro ao dar entrada no Google Sheets: {err}")
                
                if col_btn2.button("📤 Dar Saída no Estoque (Google Sheets)", use_container_width=True):
                    try:
                        sheet = conectar_gspread()
                        df_estoque = carregar_estoque_do_google()
                        
                        sucesso = True
                        for item in produtos_nota:
                            cod_nf = item["Código"]
                            qtd_nf = item["Quantidade"]
                            
                            if not df_estoque.empty and 'codigo' in df_estoque.columns:
                                mask = df_estoque['codigo'].astype(str).str.strip() == cod_nf
                                
                                if mask.any():
                                    idx_pandas = df_estoque[mask].index[0]
                                    row_number = idx_pandas + 2
                                    
                                    try:
                                        qtd_atual = float(df_estoque.loc[idx_pandas, 'qtde'])
                                    except:
                                        qtd_atual = 0.0
                                        
                                    nova_qtd = max(0.0, qtd_atual - qtd_nf)
                                    df_estoque.loc[idx_pandas, 'qtde'] = nova_qtd
                                    
                                    colunas_sheet = [str(c).strip().lower() for c in sheet.row_values(1)]
                                    if 'qtde' in colunas_sheet:
                                        col_index = colunas_sheet.index('qtde') + 1
                                        sheet.update_cell(row_number, col_index, nova_qtd)
                                else:
                                    st.warning(f"Produto {cod_nf} não encontrado no Google Sheets.")
                                    sucesso = False
                            else:
                                st.warning("A planilha do Google Sheets está vazia ou sem a coluna 'codigo'.")
                                sucesso = False
                                
                        if sucesso:
                            st.success("Saída registrada e salva no Google Sheets com sucesso!")
                            st.cache_data.clear()
                    except Exception as err:
                        st.error(f"Erro ao dar saída no Google Sheets: {err}")
                        
        except Exception as e:
            st.error(f"Erro ao processar o arquivo XML: {e}")
