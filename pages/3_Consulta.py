import streamlit as st
import pandas as pd
from database import carregar_clientes, carregar_implantacao
from datetime import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(layout="wide")
st.title("📄 Protocolo de Implantação")

# -----------------------------
# CHECKLIST PADRÃO
# -----------------------------
CHECKLISTS = {
    "Inicial": [
        "Cliente cadastrado",
        "Usuário criado",
        "Boas-vindas enviadas",
        "Reunião agendada"
    ],
    "Cadastro": [
        "Clínica cadastrada",
        "Profissionais cadastrados",
        "Serviços configurados",
        "Agenda configurada",
        "Financeiro configurado"
    ],
    "Importação de Base": [
        "Base recebida",
        "Base validada",
        "Importação realizada",
        "Validação com cliente"
    ],
    "Treinamento": [
        "Treinamento agenda",
        "Treinamento pacientes",
        "Treinamento financeiro",
        "Dúvidas resolvidas"
    ],
    "Acompanhamento Inicial": [
        "Cliente usando sistema",
        "Primeiros agendamentos",
        "Correções realizadas",
        "Uso validado"
    ],
    "Acompanhamento Final": [
        "Cliente operando sozinho",
        "Fluxo validado",
        "Feedback coletado",
        "Implantação finalizada"
    ]
}

# -----------------------------
# FUNÇÕES
# -----------------------------
def status_icon(status):
    if status == "Concluido":
        return "OK"
    elif status == "Em andamento":
        return "EM ANDAMENTO"
    elif status == "Bloqueado":
        return "BLOQUEADO"
    else:
        return "-"

def limpar_texto(texto):
    if not texto:
        return ""
    return str(texto).encode("latin-1", "ignore").decode("latin-1")

def calcular_progresso(df):
    total_itens = 0
    itens_concluidos = 0

    for _, row in df.iterrows():
        base = CHECKLISTS.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []

        total_itens += len(base)
        itens_concluidos += len([item for item in base if item in salvo])

    if total_itens == 0:
        return 0

    return int((itens_concluidos / total_itens) * 100)

def garantir_colunas(df):
    colunas = [
        "Cliente", "Etapa", "Status", "Bloqueado", "Motivo",
        "Responsavel_Etapa", "Data_Inicio", "Data_Conclusao", "Checklist"
    ]
    for col in colunas:
        if col not in df.columns:
            df[col] = ""
    return df

# -----------------------------
# CARREGAR DADOS
# -----------------------------
clientes_df = carregar_clientes().fillna("")
df = carregar_implantacao().fillna("")
df = garantir_colunas(df)

clientes_df = clientes_df.sort_values("Nome")

# -----------------------------
# BUSCA
# -----------------------------
st.subheader("📌 Cliente / Clínica")

col1, col2 = st.columns(2)

with col1:
    doc_busca = st.text_input("🔎 Buscar por CPF/CNPJ")

    if doc_busca:
        clientes_filtrados = clientes_df[
            clientes_df["CNPJ_CPF"].astype(str).str.contains(doc_busca)
        ]
    else:
        clientes_filtrados = clientes_df

# -----------------------------
# SELEÇÃO
# -----------------------------
cliente_sel = None

if doc_busca and len(clientes_filtrados) == 1:
    cliente_sel = clientes_filtrados.iloc[0]["Nome"]
    st.success(f"Cliente encontrado: {cliente_sel}")
else:
    lista_clientes = ["-- Selecione --"] + clientes_filtrados["Nome"].tolist()

    with col2:
        cliente_sel = st.selectbox("Selecione o cliente", lista_clientes)

    if cliente_sel == "-- Selecione --":
        st.warning("Selecione um cliente para continuar")
        st.stop()

doc_sel = clientes_df[
    clientes_df["Nome"] == cliente_sel
]["CNPJ_CPF"].values[0]

df_cliente = df[df["Cliente"] == cliente_sel].copy()

# -----------------------------
# PROGRESSO REAL
# -----------------------------
progresso = calcular_progresso(df_cliente)

st.progress(progresso)
st.write(f"Progresso Geral: **{progresso}%**")

# -----------------------------
# VISUAL
# -----------------------------
col1, col2 = st.columns(2)

for i, (_, row) in enumerate(df_cliente.iterrows()):
    container = col1 if i % 2 == 0 else col2

    with container:
        st.markdown(f"""
        ### {status_icon(row["Status"])} {row["Etapa"]}

        **Status:** {row["Status"]}  
        **Responsável:** {row["Responsavel_Etapa"]}  
        **Início:** {row["Data_Inicio"]}  
        **Conclusão:** {row["Data_Conclusao"]}  
        """)

        if row["Bloqueado"] == "Sim":
            st.error(f"🚨 Motivo: {row['Motivo']}")

        base = CHECKLISTS.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []

        if base:
            st.markdown("**Checklist:**")
            for item in base:
                if item in salvo:
                    st.write(f"✔ {item}")
                else:
                    st.write(f"⬜ {item}")

# -----------------------------
# PDF
# -----------------------------
class PDF(FPDF):

    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)

        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "PROTOCOLO DE IMPLANTACAO", 0, 1, "C")
        self.ln(5)

    def barra_progresso(self, progresso):
        self.set_fill_color(200, 200, 200)
        self.cell(0, 8, "", 1, 1)

        largura = (progresso / 100) * 190

        self.set_fill_color(0, 102, 204)
        self.set_xy(10, self.get_y() - 8)
        self.cell(largura, 8, "", 0, 1, "L", True)

        self.ln(3)
        self.set_font("Arial", "", 10)
        self.cell(0, 5, f"Progresso: {progresso}%", 0, 1)

def gerar_pdf(df_cliente, cliente, progresso, doc_sel):

    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", "", 11)

    pdf.cell(0, 6, f"Cliente: {limpar_texto(cliente)}", 0, 1)
    pdf.cell(0, 6, f"Documento: {limpar_texto(doc_sel)}", 0, 1)
    pdf.cell(0, 6, f"Data: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)

    pdf.ln(3)
    pdf.barra_progresso(progresso)
    pdf.ln(5)

    for _, row in df_cliente.iterrows():

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"{limpar_texto(status_icon(row['Status']))} {limpar_texto(row['Etapa'])}", 0, 1)

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Status: {limpar_texto(row['Status'])}", 0, 1)
        pdf.cell(0, 5, f"Responsavel: {limpar_texto(row['Responsavel_Etapa'])}", 0, 1)
        pdf.cell(0, 5, f"Inicio: {limpar_texto(row['Data_Inicio'])} | Conclusao: {limpar_texto(row['Data_Conclusao'])}", 0, 1)

        if row["Bloqueado"] == "Sim":
            pdf.set_text_color(200, 0, 0)
            pdf.multi_cell(0, 5, f"Motivo: {limpar_texto(row['Motivo'])}")
            pdf.set_text_color(0, 0, 0)

        base = CHECKLISTS.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []

        if base:
            pdf.cell(0, 5, "Checklist:", 0, 1)
            for item in base:
                if item in salvo:
                    pdf.cell(0, 5, f"[X] {limpar_texto(item)}", 0, 1)
                else:
                    pdf.cell(0, 5, f"[ ] {limpar_texto(item)}", 0, 1)

        pdf.ln(3)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)

    return tmp.name

# -----------------------------
# BOTÃO FINAL (SIMPLES)
# -----------------------------
st.markdown("---")

if st.button("📄 Gerar Protocolo Executivo"):
    pdf_path = gerar_pdf(df_cliente, cliente_sel, progresso, doc_sel)

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇️ Baixar Protocolo",
            data=f.read(),
            file_name=f"protocolo_{cliente_sel}.pdf",
            mime="application/pdf"
        )