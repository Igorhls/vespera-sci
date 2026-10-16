"""
Funções de sanitização de dados colados do Excel, formatação numérica no padrão
brasileiro e cálculo de estatísticas descritivas.
"""

import numpy as np
import pandas as pd


def sanitizar_dados_tabela(df: pd.DataFrame):
    """
    Corrige automaticamente problemas comuns ao colar dados de temperatura do Excel em PT-BR:
    1. Vírgula que virou centena/milhar (ex: 27,4 -> 274.0 vira 27.4).
    2. Valores vazios na coluna 'Pontos' preenchidos como P1..Pn.
    """
    modificado = False
    df_novo = df.copy()

    for idx in range(len(df_novo)):
        val_ponto = df_novo.iloc[idx]["Pontos"]
        if pd.isna(val_ponto) or str(val_ponto).strip().lower() in ["none", "nan", ""]:
            df_novo.iloc[idx, df_novo.columns.get_loc("Pontos")] = f"P{idx + 1}"
            modificado = True

    for col in ["Manha", "Tarde", "Noite"]:
        if col in df_novo.columns:
            for idx in range(len(df_novo)):
                val = df_novo.iloc[idx][col]
                if pd.notnull(val):
                    try:
                        v_float = float(str(val).replace(",", "."))
                        if 60.0 < v_float <= 600.0:
                            df_novo.iloc[idx, df_novo.columns.get_loc(col)] = round(v_float / 10.0, 1)
                            modificado = True
                        elif 600.0 < v_float <= 6000.0:
                            df_novo.iloc[idx, df_novo.columns.get_loc(col)] = round(v_float / 100.0, 1)
                            modificado = True
                        else:
                            df_novo.iloc[idx, df_novo.columns.get_loc(col)] = v_float
                    except (ValueError, TypeError):
                        pass

    return df_novo, modificado


def sanitizar_dados_barras(df: pd.DataFrame):
    """Sanitiza a tabela de Média e Desvio Padrão (TA)."""
    modificado = False
    df_novo = df.copy()

    for idx in range(len(df_novo)):
        val_mes = df_novo.iloc[idx]["Mes"]
        if pd.isna(val_mes) or str(val_mes).strip().lower() in ["none", "nan", ""]:
            df_novo.iloc[idx, df_novo.columns.get_loc("Mes")] = f"Mês {idx + 1}"
            modificado = True

    cols_num = ["Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
    for col in cols_num:
        if col in df_novo.columns:
            for idx in range(len(df_novo)):
                val = df_novo.iloc[idx][col]
                if pd.notnull(val):
                    try:
                        v_float = float(str(val).replace(",", "."))
                        if 100.0 < v_float <= 1000.0:
                            df_novo.iloc[idx, df_novo.columns.get_loc(col)] = round(v_float / 10.0, 2)
                            modificado = True
                        elif 1000.0 < v_float <= 10000.0:
                            df_novo.iloc[idx, df_novo.columns.get_loc(col)] = round(v_float / 100.0, 2)
                            modificado = True
                        else:
                            df_novo.iloc[idx, df_novo.columns.get_loc(col)] = v_float
                    except (ValueError, TypeError):
                        pass

    return df_novo, modificado


def formatar_numero_ptbr(valor, modo_formato: str = "Automático (ex: 27,32 | 2,3)") -> str:
    """Formata um número float com vírgula decimal no padrão brasileiro (ex: 27,32 ou 2,3)."""
    if pd.isna(valor):
        return ""
    if "Fixas" in modo_formato:
        return f"{float(valor):.2f}".replace(".", ",")
    texto = f"{float(valor):.2f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def calcular_estatisticas_serie(valores) -> dict:
    """Retorna média, desvio padrão amostral, mínimo, máximo, amplitude e N de uma série."""
    s = pd.to_numeric(pd.Series(valores), errors="coerce").dropna()
    if s.empty:
        return {}
    return {
        "n": int(len(s)),
        "media": float(s.mean()),
        "desvio": float(s.std(ddof=1)) if len(s) >= 2 else 0.0,
        "minimo": float(s.min()),
        "maximo": float(s.max()),
        "amplitude": float(s.max() - s.min()),
    }
