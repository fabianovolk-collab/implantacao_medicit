import pandas as pd
import os

ARQUIVO_CLIENTES = "clientes.csv"
ARQUIVO_IMPLANTACAO = "implantacao.csv"

# =============================
# CLIENTES
# =============================
def carregar_clientes():

    if os.path.exists(ARQUIVO_CLIENTES):
        df = pd.read_csv(ARQUIVO_CLIENTES, dtype=str)
    else:
        df = pd.DataFrame(columns=[
            "Tipo_Pessoa",
            "CNPJ_CPF",
            "Nome",
            "Telefone",
            "Responsavel_Comercial",
            "Responsavel_Cliente",
            "Responsavel_Medicit"
        ])

    colunas = [
        "Tipo_Pessoa",
        "CNPJ_CPF",
        "Nome",
        "Telefone",
        "Responsavel_Comercial",
        "Responsavel_Cliente",
        "Responsavel_Medicit"
    ]

    for col in colunas:
        if col not in df.columns:
            df[col] = ""

    return df


def salvar_clientes(df):
    df.to_csv(ARQUIVO_CLIENTES, index=False)


# =============================
# IMPLANTAÇÃO (NOVO MODELO)
# =============================
def carregar_implantacao():

    if os.path.exists(ARQUIVO_IMPLANTACAO):
        df = pd.read_csv(ARQUIVO_IMPLANTACAO, dtype=str)
    else:
        df = pd.DataFrame()

    # 🔥 NOVO PADRÃO DE COLUNAS
    colunas = [
        "CNPJ_CPF",
        "Cliente",
        "Etapa",
        "Status",
        "Data_Inicio",
        "Data_Prevista",
        "Data_Conclusao",
        "Responsavel_Etapa",
        "Bloqueado",
        "Motivo_Bloqueio",
        "Proxima_Acao",
        "Checklist",
        "Ultima_Atualizacao"
    ]

    # 🔄 MIGRAÇÃO AUTOMÁTICA (se existir modelo antigo)
    if not df.empty:

        if "Fase" in df.columns:
            df["Etapa"] = df["Fase"]

        if "Responsavel" in df.columns:
            df["Responsavel_Etapa"] = df["Responsavel"]

        if "Previsao_Inicio" in df.columns:
            df["Data_Prevista"] = df["Previsao_Inicio"]

        if "Observacoes" in df.columns:
            df["Proxima_Acao"] = df["Observacoes"]

    # GARANTIR TODAS AS COLUNAS
    for col in colunas:
        if col not in df.columns:
            df[col] = ""

    return df


def salvar_implantacao(df):
    df.to_csv(ARQUIVO_IMPLANTACAO, index=False)