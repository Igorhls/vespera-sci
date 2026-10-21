"""
Funções de sanitização de dados colados do Excel, formatação numérica no padrão
brasileiro e cálculo de estatísticas descritivas.
"""

import numpy as np
import pandas as pd


def sanitizar_dados_tabela(df: pd.DataFrame):
    """
    Corrige automaticamente problemas comuns ao colar dados de temperatura/medições do Excel em PT-BR:
    1. Vírgula que virou centena/milhar (ex: 27,4 -> 274.0 vira 27.4).
    2. Valores vazios na coluna identificadora preenchidos como P1..Pn.
    Compatível com qualquer número de colunas/séries dinâmicas.
    """
    modificado = False
    df_novo = df.copy()
    if df_novo.empty:
        return df_novo, False

    col_pontos = "Pontos" if "Pontos" in df_novo.columns else df_novo.columns[0]
    for idx in range(len(df_novo)):
        val_ponto = df_novo.iloc[idx][col_pontos]
        if pd.isna(val_ponto) or str(val_ponto).strip().lower() in ["none", "nan", ""]:
            df_novo.iloc[idx, df_novo.columns.get_loc(col_pontos)] = f"P{idx + 1}"
            modificado = True

    cols_num = [c for c in df_novo.columns if c != col_pontos]
    for col in cols_num:
        for idx in range(len(df_novo)):
            val = df_novo.iloc[idx][col]
            if pd.notnull(val) and val != "":
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


def sanitizar_dados_dispersao(df: pd.DataFrame):
    """Sanitiza a tabela de Dispersão / Regressão (Ponto, X, Y)."""
    modificado = False
    df_novo = df.copy()

    col_ponto = "Ponto" if "Ponto" in df_novo.columns else df_novo.columns[0]
    for idx in range(len(df_novo)):
        val_ponto = df_novo.iloc[idx][col_ponto]
        if pd.isna(val_ponto) or str(val_ponto).strip().lower() in ["none", "nan", ""]:
            df_novo.iloc[idx, df_novo.columns.get_loc(col_ponto)] = f"P{idx + 1}"
            modificado = True

    for col in ["X", "Y"]:
        if col in df_novo.columns:
            for idx in range(len(df_novo)):
                val = df_novo.iloc[idx][col]
                if pd.notnull(val):
                    try:
                        v_float = float(str(val).replace(",", "."))
                        df_novo.iloc[idx, df_novo.columns.get_loc(col)] = v_float
                    except (ValueError, TypeError):
                        pass

    return df_novo, modificado


def calcular_regressao_linear(x_vals, y_vals) -> dict:
    """
    Calcula parâmetros científicos completos de Regressão Linear Simples:
    - Inclinação (a) e Intercepto (b): y = ax + b
    - Coeficiente de correlação de Pearson (r)
    - Coeficiente de determinação (R²)
    - Erro padrão da estimativa (Se)
    - Média e desvio padrão de X e Y
    - Interpretação textual acadêmica
    """
    s_x = pd.to_numeric(pd.Series(x_vals), errors="coerce")
    s_y = pd.to_numeric(pd.Series(y_vals), errors="coerce")
    valido = (~s_x.isna()) & (~s_y.isna())
    x = s_x[valido].to_numpy(dtype=float)
    y = s_y[valido].to_numpy(dtype=float)

    n = len(x)
    if n < 2:
        return {}

    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    ss_xx = float(np.sum((x - x_mean) ** 2))
    ss_yy = float(np.sum((y - y_mean) ** 2))
    ss_xy = float(np.sum((x - x_mean) * (y - y_mean)))

    if ss_xx <= 0:
        return {}

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    r = ss_xy / np.sqrt(ss_xx * ss_yy) if (ss_xx > 0 and ss_yy > 0) else 0.0
    r = max(-1.0, min(1.0, float(r)))
    r2 = float(r ** 2)

    y_pred = slope * x + intercept
    residuos = y - y_pred
    se = float(np.sqrt(np.sum(residuos ** 2) / (n - 2))) if n > 2 else 0.0

    # Formatação de equação
    sinal = " + " if intercept >= 0 else " - "
    eq_str = f"y = {slope:.4f}x{sinal}{abs(intercept):.4f}".replace(".", ",")
    eq_curta = f"y = {slope:.3f}x{sinal}{abs(intercept):.3f}".replace(".", ",")

    # Classificação da correlação
    abs_r = abs(r)
    if abs_r >= 0.8:
        forca = "Muito Forte"
    elif abs_r >= 0.6:
        forca = "Forte"
    elif abs_r >= 0.4:
        forca = "Moderada"
    elif abs_r >= 0.2:
        forca = "Fraca"
    else:
        forca = "Muito Fraca ou Nula"

    direcao = "Positiva (Direta)" if r > 0 else "Negativa (Inversa)"
    pct_var = r2 * 100.0

    interpretacao = (
        f"{pct_var:.1f}% da variação da variável Y é explicada pela variação de X. "
        f"Evidência de relação {direcao.lower()} {forca.lower()} entre as variáveis."
    )

    return {
        "n": n,
        "slope": slope,
        "intercept": intercept,
        "r": r,
        "r2": r2,
        "se": se,
        "equacao": eq_str,
        "equacao_curta": eq_curta,
        "r2_formatado": f"{r2:.3f}".replace(".", ","),
        "r_formatado": f"{r:.4f}".replace(".", ","),
        "forca": forca,
        "direcao": direcao,
        "interpretacao": interpretacao,
        "media_x": x_mean,
        "desvio_x": float(np.std(x, ddof=1)) if n > 1 else 0.0,
        "min_x": float(np.min(x)),
        "max_x": float(np.max(x)),
        "media_y": y_mean,
        "desvio_y": float(np.std(y, ddof=1)) if n > 1 else 0.0,
        "min_y": float(np.min(y)),
        "max_y": float(np.max(y)),
    }



def calcular_estatisticas_boxplot(valores) -> dict:
    """Calcula estatísticas de distribuição para Boxplot: quartis, mediana, IQR e outliers."""
    s = pd.to_numeric(pd.Series(valores), errors="coerce").dropna()
    if s.empty:
        return {}
    q1 = float(s.quantile(0.25))
    mediana = float(s.median())
    q3 = float(s.quantile(0.75))
    iqr = float(q3 - q1)
    lower_b = q1 - 1.5 * iqr
    upper_b = q3 + 1.5 * iqr
    outliers = [float(v) for v in s[(s < lower_b) | (s > upper_b)].tolist()]
    return {
        "n": int(len(s)),
        "media": float(s.mean()),
        "desvio": float(s.std(ddof=1)) if len(s) >= 2 else 0.0,
        "minimo": float(s.min()),
        "maximo": float(s.max()),
        "q1": q1,
        "mediana": mediana,
        "q3": q3,
        "iqr": iqr,
        "limite_inferior": lower_b,
        "limite_superior": upper_b,
        "outliers": outliers,
    }
