import streamlit as st
import pandas as pd
from database import carregar_clientes, carregar_implantacao
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
import base64

st.set_page_config(layout="wide")
st.title("📄 Protocolo de Implantação")

# -----------------------------
# CHECKLIST
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
    "Go-Live": [
        "Data de virada definida",
        "Sistema liberado para uso oficial",
        "Equipe alinhada",
        "Primeiro dia de operação realizado"
    ],
    "Acompanhamento": [
        "Cliente utilizando sistema no dia a dia",
        "Ajustes realizados",
        "Fluxo validado",
        "Cliente operando com autonomia",
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
    elif status == "Bloqueado/Pendente":
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
        "Cliente", "Etapa", "Status", "Motivo",
        "Responsavel_Etapa", "Responsavel_Cliente",
        "Participantes",
        "Data_Inicio", "Data_Conclusao", "Checklist"
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

df["Etapa"] = df["Etapa"].replace({
    "Acompanhamento Inicial": "Acompanhamento",
    "Acompanhamento Final": "Acompanhamento"
})

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
# PROGRESSO
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
        **Responsável Medicit:** {row["Responsavel_Etapa"]}  
        **Responsável Cliente:** {row["Responsavel_Cliente"]}  
        **Participantes:** {row["Participantes"]}  
        **Início:** {row["Data_Inicio"]}  
        **Conclusão:** {row["Data_Conclusao"]}  
        """)

        if row["Status"] == "Bloqueado/Pendente":
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
# PDF FINAL AJUSTADO
# -----------------------------
class PDF(FPDF):

    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)

        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Protocolo Implantacao", 0, 1, "C")

        self.ln(10)  # 🔥 espaço maior abaixo da logo

        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, "C")

    def barra(self, percentual):
        # Fundo da barra (contorno)
        self.set_fill_color(255, 255, 255)
        self.cell(0, 6, "", 1, 1)

        if percentual <= 0:
            self.ln(2)
            return

        largura = (percentual / 100) * 190

        # 🎨 Definição de cor por status
        if percentual == 100:
            cor = (0, 176, 80)       # Verde
        elif percentual > 50:
            cor = (0, 102, 204)      # Azul
        else:
            cor = (255, 192, 0)      # Amarelo

        self.set_fill_color(*cor)

        # Posiciona dentro da barra
        self.set_xy(10, self.get_y() - 6)
        self.cell(largura, 6, "", 0, 1, "L", True)

        self.ln(2)


def progresso_etapa(row):
    base = CHECKLISTS.get(row["Etapa"], [])
    salvo = row["Checklist"].split("|") if row["Checklist"] else []

    if len(base) == 0:
        return 0

    feitos = len([item for item in base if item in salvo])
    return int((feitos / len(base)) * 100)


def gerar_pdf(df_cliente, cliente, progresso, doc_sel):

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 11)

    data_inicio_implantacao = df_cliente["Data_Inicio"].replace("", None).dropna().min()

    pdf.cell(0, 6, f"Cliente: {limpar_texto(cliente)}", 0, 1)
    pdf.cell(0, 6, f"CPF/CNPJ: {limpar_texto(doc_sel)}", 0, 1)
    pdf.cell(0, 6, f"Data Inicio Implantacao: {limpar_texto(data_inicio_implantacao)}", 0, 1)

    pdf.ln(3)

    pdf.cell(0, 5, f"Progresso Geral: {progresso}%", 0, 1)
    pdf.barra(progresso)

    pdf.ln(3)

    for _, row in df_cliente.iterrows():

        prog = progresso_etapa(row)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"Etapa: {limpar_texto(row['Etapa'])}", 0, 1)

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Status: {limpar_texto(row['Status'])}", 0, 1)
        pdf.cell(0, 5, f"Responsavel Medicit: {limpar_texto(row['Responsavel_Etapa'])}", 0, 1)
        pdf.cell(0, 5, f"Responsavel Cliente: {limpar_texto(row['Responsavel_Cliente'])}", 0, 1)
        pdf.cell(0, 5, f"Participantes: {limpar_texto(row['Participantes'])}", 0, 1)
        pdf.cell(0, 5, f"Data Inicio Etapa: {limpar_texto(row['Data_Inicio'])}", 0, 1)

        if row["Status"] == "Bloqueado/Pendente":
            pdf.set_text_color(200, 0, 0)
            pdf.multi_cell(0, 5, f"Motivo Bloqueio/Pendencia: {limpar_texto(row['Motivo'])}")
            pdf.set_text_color(0, 0, 0)

        pdf.ln(2)

        base = CHECKLISTS.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []

        pdf.cell(0, 5, "Checklist:", 0, 1)

        for item in base:
            if item in salvo:
                pdf.cell(0, 5, f"[X] {limpar_texto(item)}", 0, 1)
            else:
                pdf.cell(0, 5, f"[ ] {limpar_texto(item)}", 0, 1)

        pdf.ln(2)

        status_texto = (
            "Não iniciado" if prog == 0 else
            "Em risco" if prog <= 50 else
            "Em andamento" if prog < 100 else
            "Concluído"
        )

        pdf.cell(0, 5, f"Progresso Etapa: {prog}% - {status_texto}", 0, 1)
        pdf.barra(prog)

        # 🔥 LINHA ENTRE ETAPAS
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)

    return tmp.name


# -----------------------------
# BOTÃO FINAL
# -----------------------------
st.markdown("---")

if st.button("📄 Gerar Protocolo Executivo"):
    pdf_path = gerar_pdf(df_cliente, cliente_sel, progresso, doc_sel)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    b64 = base64.b64encode(pdf_bytes).decode()

    href = f'''
    <html>
        <body>
            <a id="download_link" href="data:application/pdf;base64,{b64}" download="protocolo_{cliente_sel}.pdf"></a>
            <script>
                document.getElementById('download_link').click();
            </script>
        </body>
    </html>
    '''

    st.components.v1.html(href, height=0)
    st.success("📄 Protocolo gerado com sucesso!")