import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Consultas Defran", layout="centered")

# --- EXIBIR LOGO DA EMPRESA NO TOPO ---
if os.path.exists("navbar-logo.jpg"):
    st.image("navbar-logo.jpg", width=300)
elif os.path.exists("navbar-logo.png"):
    st.image("navbar-logo.png", width=300)

st.title("Consultas Defran")
st.markdown("---")

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
        caminho = f"dados/{arquivo}"
        if os.path.exists(caminho):
            dados[nome] = pd.read_csv(caminho, sep=';', encoding='latin1', names=colunas_prod, header=0)
    dados["Estoque Defran"] = carregar_estoque_do_google()
    
    # Carregar Clientes
    caminho_clientes = "dados/clientes.csv"
    if os.path.exists(caminho_clientes):
        dados["Clientes"] = pd.read_csv(caminho_clientes, sep=',', encoding='latin1')
    else:
        dados["Clientes"] = pd.DataFrame()
        
    return dados

dados_carregados = carregar_dados()

# --- FUNÇÃO PARA LER O BANCO DE DADOS DE PRODUTOS/ESPECIFICAÇÕES ---
def carregar_base_produtos_txt():
    caminho = "docs/produtos_info.txt"
    produtos_dict = {}
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        blocos = conteudo.split("\n\n")
        for bloco in blocos:
            linhas = bloco.strip().split("\n")
            dados_item = {}
            ref_encontrada = ""
            for linha in linhas:
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    chave_limpa = chave.strip().lower()
                    valor_limpo = valor.strip()
                    if "referência" in chave_limpa:
                        ref_encontrada = valor_limpo
                        dados_item["referencia"] = valor_limpo
                    elif "descrição" in chave_limpa:
                        dados_item["descricao"] = valor_limpo
                    elif "prazo de entrega" in chave_limpa:
                        dados_item["prazo"] = valor_limpo
                    elif "fator de segurança" in chave_limpa:
                        dados_item["fator"] = valor_limpo
                    elif "ncm" in chave_limpa:
                        dados_item["ncm"] = valor_limpo
                    elif "icms" in chave_limpa:
                        dados_item["icms"] = valor_limpo
                    elif "ipi" in chave_limpa:
                        dados_item["ipi"] = valor_limpo
            if ref_encontrada:
                produtos_dict[ref_encontrada.lower()] = dados_item
    return produtos_dict

base_produtos = carregar_base_produtos_txt()

# --- INTERFACE COM ÍCONES NAS ABAS ---
aba1, aba2, aba3, aba4 = st.tabs([
    "🔗 Produtos", 
    "📦 Estoque Defran", 
    "🏗️ Carga de Trabalho",
    "📋 Orçamento"
])

with aba1:
    selecao = st.selectbox("Escolha a base:", ["Produtos Gunnebo", "Produtos Crosby", "Manilhas Crosby"])
    if selecao in dados_carregados:
        df = dados_carregados[selecao]
        termo = st.text_input("Filtrar referência (Produtos):")
        if termo:
            df = df[df['ref_prod'].astype(str).str.contains(termo, case=False, na=False)]
        st.dataframe(df, use_container_width=True)

with aba2:
    st.header("Estoque Defran")
    termo_busca = st.text_input("🔍 Filtrar por código ou referência:", key="busca_estoque")
    df_est = dados_carregados["Estoque Defran"]
    if st.session_state.get("busca_estoque"):
        termo = st.session_state.busca_estoque
        df_est = df_est[df_est['codigo'].astype(str).str.contains(termo, case=False) | df_est['ref_prod'].astype(str).str.contains(termo, case=False)]
    event = st.dataframe(df_est, use_container_width=True, on_select="rerun", selection_mode="single-row")

    if "ultima_selecao" not in st.session_state:
        st.session_state.ultima_selecao = None
    if event.selection.rows:
        st.session_state.ultima_selecao = event.selection.rows[0]

    dados_padrao = {"id": "", "codigo": "", "ref_prod": "", "qtde": 0.0, "desc_prod": ""}
    if st.session_state.ultima_selecao is not None:
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
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- ABA 3: CARGA DE TRABALHO LINGAS ---
with aba3:
    st.header("")
    
    caminho_pdf = "docs/cargaTrabalhoLingas.pdf"
    
    if os.path.exists(caminho_pdf):
        with open(caminho_pdf, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Exibe o PDF diretamente na tela via visualizador embutido (iframe)
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Botão opcional para download direto
        with open(caminho_pdf, "rb") as f:
            st.download_button(
                label="📥 Baixar PDF de Carga de Trabalho",
                data=f,
                file_name="cargaTrabalhoLingas.pdf",
                mime="application/pdf"
            )
    else:
        st.error(f"O arquivo PDF não foi encontrado no caminho: {caminho_pdf}. Verifique se a pasta 'docs' e o arquivo estão sincronizados no GitHub.")


# --- ABA 4: CADASTRO DE ORÇAMENTO ---
with aba4:
    st.header("📋 Cadastro e Geração de Orçamento")
    
    df_clientes = dados_carregados.get("Clientes", pd.DataFrame())
    lista_razoes = [""] + list(df_clientes['razao'].unique()) if not df_clientes.empty else [""]
    
    # Seleção de cliente para preenchimento automático
    cliente_selecionado = st.selectbox("Selecione o Cliente na Base:", lista_razoes)
    
    dados_cli = {}
    if cliente_selecionado and not df_clientes.empty:
        match = df_clientes[df_clientes['razao'] == cliente_selecionado]
        if not match.empty:
            dados_cli = match.iloc[0].to_dict()

    col_c1, col_c2, col_c3 = st.columns(3)
    num_orc = col_c1.text_input("Nº da Proposta", value="373/26")
    data_orc = col_c2.text_input("Data", value="19 de agosto de 2026")
    cliente_orc = col_c3.text_input("Cliente", value=str(dados_cli.get("razao", "SIVA")))
    
    col_c4, col_c5, col_c6 = st.columns(3)
    cidade_orc = col_c4.text_input("Cidade", value=str(dados_cli.get("cidade", "ITAQUAQUECETUBA")))
    estado_orc = col_c5.text_input("Estado", value=str(dados_cli.get("estado", "SP")))
    tel_orc = col_c6.text_input("Telefone", value=str(dados_cli.get("telefone", "(11) 4646-4646")))

    col_c7, col_c8 = st.columns(2)
    contato_orc = col_c7.text_input("Contato", value=str(dados_cli.get("contato", "MARCELO")))
    email_orc = col_c8.text_input("E-mail", value=str(dados_cli.get("email", "compras@siva.com.br")))
    vendedor_orc = st.text_input("Vendedor(a)", value="BEATRIZ")

    st.markdown("---")
    st.subheader("Adicionar Itens ao Orçamento (Produtos ou Lingas)")
    
    ref_digitada = st.selectbox("Buscar Referência Automática (Opcional):", [""] + list(base_produtos.keys()))
    dados_encontrados = base_produtos.get(ref_digitada, {}) if ref_digitada else {}

    with st.form("form_item_orc", clear_on_submit=True):
        col_t1, col_t2 = st.columns(2)
        tipo_item = col_t1.selectbox("Tipo de Item", ["Produto", "Linga"])
        item_ref = col_t2.text_input("Referência Exata", value=dados_encontrados.get("referencia", ""))

        col_i1, col_i2, col_i3 = st.columns(3)
        item_qtd = col_i1.number_input("Quantidade / Metragem", min_value=0.01, value=1.00, step=0.01)
        item_unidade = col_i2.selectbox("Unidade", ["PÇ", "M"], index=0)
        item_val = col_i3.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0, step=0.10)
        
        item_desc = st.text_area("Descrição Completa", value=dados_encontrados.get("descricao", ""))
        
        col_extra1, col_extra2, col_extra3, col_extra4 = st.columns(4)
        item_prazo = col_extra1.text_input("Prazo de Entrega", value=dados_encontrados.get("prazo", "05 dias"))
        item_ncm = col_extra2.text_input("NCM", value=dados_encontrados.get("ncm", "73269090"))
        item_ipi = col_extra3.text_input("IPI", value=dados_encontrados.get("ipi", "5% Incluso"))
        item_fator = col_extra4.text_input("Fator de Seg.", value=dados_encontrados.get("fator", "4:1"))
        
        add_item_btn = st.form_submit_button("Adicionar Item na Proposta")
        
        if add_item_btn and item_ref:
            if "itens_orcamento" not in st.session_state:
                st.session_state.itens_orcamento = []
                
            st.session_state.itens_orcamento.append({
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
            })
            st.success("Item adicionado com sucesso!")
            st.rerun()

    if "itens_orcamento" in st.session_state and st.session_state.itens_orcamento:
        st.write("### Itens Na Proposta:")
        df_itens = pd.DataFrame(st.session_state.itens_orcamento)
        st.dataframe(df_itens[['tipo', 'referencia', 'quantidade', 'unidade', 'unitario', 'total']], use_container_width=True)
        
        if st.button("🗑️ Limpar Todos os Itens"):
            st.session_state.itens_orcamento = []
            st.rerun()
            
        st.markdown("---")
        
        def gerar_pdf_defran(num, data, cliente, cidade, estado, tel, contato, email, vendedor, itens):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            elementos = []
            styles = getSampleStyleSheet()
            
            estilo_empresa = ParagraphStyle('Empresa', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.HexColor("#333333"))
            estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading2'], fontSize=12, leading=14, textColor=colors.HexColor("#0056b3"), alignment=1)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#222222"))
            estilo_bold = ParagraphStyle('Bold', parent=estilo_texto, fontName='Helvetica-Bold')
            
            # Cabeçalho Empresa
            elementos.append(Paragraph("<b>DEFRAN - PRODUTOS PARA MOVIMENTAÇÃO DE CARGAS LTDA</b>", estilo_empresa))
            elementos.append(Paragraph("Av. Getúlio Vargas, 966 Bambu/Porto Feliz-SP/CEP: 18540-380", estilo_empresa))
            elementos.append(Paragraph("CNPJ: 66.521.337/0001-52 / IE: 554.109.111.113 | KITO CROSBY | GUNNEBO REVENDEDOR", estilo_empresa))
            elementos.append(Spacer(1, 10))
            
            elementos.append(Paragraph("<b>PROPOSTA COMERCIAL</b>", estilo_titulo))
            elementos.append(Spacer(1, 8))
            
            info_dados = [
                [Paragraph(f"<b>PROPOSTA N°:</b> {num}", estilo_texto), Paragraph(f"Porto Feliz, {data}", estilo_texto)],
                [Paragraph(f"<b>CLIENTE:</b> {cliente}", estilo_texto), Paragraph(f"<b>VENDEDOR(A):</b> {vendedor}", estilo_texto)],
                [Paragraph(f"<b>CIDADE:</b> {cidade} - {estado}", estilo_texto), Paragraph(f"<b>CONTATO:</b> {contato}", estilo_texto)],
                [Paragraph(f"<b>TEL:</b> {tel}", estilo_texto), Paragraph(f"<b>E-MAIL:</b> {email}", estilo_texto)]
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
                    [Paragraph(f"<b>Item: {idx:02d} ({item['tipo']})</b>", estilo_bold), Paragraph(f"<b>Quantidade:</b> {item['quantidade']:.2f} {item['unidade']}", estilo_bold)],
                    [Paragraph(f"<b>Referência:</b> {item['referencia']}", estilo_texto), Paragraph(f"<b>Preço Unit.:</b> R$ {item['unitario']:.2f}", estilo_bold)],
                    [Paragraph(f"<b>Descrição:</b> {item['descricao']}", estilo_texto), Paragraph("", estilo_texto)],
                    [Paragraph(f"<b>Prazo de Entrega:</b> {item['prazo']}", estilo_texto), Paragraph(f"<b>NCM:</b> {item['ncm']}", estilo_texto)],
                    [Paragraph("<b>ICMS:</b> 18% Incluso", estilo_texto), Paragraph(f"<b>IPI:</b> {item['ipi']}", estilo_texto)],
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
                [Paragraph("• <b>Condição de Pagamento:</b> 30 DDL (após aprovação do cadastro)", estilo_texto)],
                [Paragraph("• <b>Condição de Entrega:</b> FOB - Posto na transportadora em Porto Feliz/SP", estilo_texto)],
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

        if st.button("📄 Gerar e Baixar Proposta Comercial em PDF"):
            pdf_buffer = gerar_pdf_defran(
                num_orc, data_orc, cliente_orc, 
                cidade_orc, estado_orc, tel_orc, contato_orc, 
                email_orc, vendedor_orc, st.session_state.itens_orcamento
            )
            st.download_button(
                label="📥 Baixar PDF do Orçamento Defran",
                data=pdf_buffer,
                file_name=f"Orcamento_{num_orc.replace('/', '-')}_{cliente_orc}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
