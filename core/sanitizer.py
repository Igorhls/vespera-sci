"""
Funções de sanitização de dados colados do Excel, formatação numérica no padrão
brasileiro e cálculo de estatísticas descritivas.
"""

import numpy as np
import pandas as pd


def corrigir_escala_valor(v: float, limite_inferior: float = 60.0) -> float:
    """
    Desfaz a perda da vírgula decimal ao colar medições do Excel em PT-BR (ex: 27,4 -> 274 -> 27,4).
    Só deve ser aplicada quando o usuário confirmar explicitamente que os dados sofreram essa perda.
    """
    if limite_inferior < v <= limite_inferior * 10.0:
        return round(v / 10.0, 1)
    if limite_inferior * 10.0 < v <= limite_inferior * 100.0:
        return round(v / 100.0, 1)
    return v


def detectar_escala_suspeita(textos, limite_inferior: float = 60.0) -> bool:
    """
    Indica se um bloco colado parece ter perdido a vírgula decimal: todos os números são inteiros
    (sem separador decimal) e ao menos um cai na faixa que seria corrigida por corrigir_escala_valor.
    """
    inteiros_suspeitos = 0
    for txt in textos:
        t = str(txt).strip()
        if not t:
            continue
        try:
            v = float(t.replace(",", "."))
        except ValueError:
            continue
        if "," in t or "." in t:
            return False
        if corrigir_escala_valor(v, limite_inferior) != v:
            inteiros_suspeitos += 1
    return inteiros_suspeitos > 0


def _normalizar_ids(df: pd.DataFrame, col_id: str, prefixo: str) -> bool:
    modificado = False
    for idx in range(len(df)):
        val = df.iloc[idx][col_id]
        if pd.isna(val) or str(val).strip().lower() in ["none", "nan", ""]:
            df.iloc[idx, df.columns.get_loc(col_id)] = f"{prefixo}{idx + 1}"
            modificado = True
    return modificado


def _normalizar_numericos(df: pd.DataFrame, colunas, corrigir_escala: bool, limite_inferior: float) -> bool:
    modificado = False
    for col in colunas:
        if col not in df.columns:
            continue
        convertidos = []
        for val in df[col].tolist():
            if pd.isna(val) or val == "":
                convertidos.append(np.nan)
                continue
            try:
                v_float = float(str(val).replace(",", "."))
            except (ValueError, TypeError):
                convertidos.append(np.nan)
                continue
            if corrigir_escala:
                v_corr = corrigir_escala_valor(v_float, limite_inferior)
                if v_corr != v_float:
                    modificado = True
                v_float = v_corr
            convertidos.append(v_float)
        df[col] = pd.Series(convertidos, index=df.index, dtype=float)
    return modificado


def sanitizar_dados_tabela(df: pd.DataFrame, corrigir_escala: bool = False):
    """
    Normaliza a tabela de séries (qualquer número de colunas):
    1. Converte textos com vírgula decimal em float.
    2. Preenche identificadores vazios como P1..Pn.
    3. Opcionalmente (corrigir_escala=True) desfaz a perda da vírgula decimal (274 -> 27,4).
       Nunca é aplicado sem confirmação do usuário, pois altera dados legítimos (ex: 1013 hPa).
    """
    df_novo = df.copy()
    if df_novo.empty:
        return df_novo, False

    col_pontos = "Pontos" if "Pontos" in df_novo.columns else df_novo.columns[0]
    modificado = _normalizar_ids(df_novo, col_pontos, "P")
    cols_num = [c for c in df_novo.columns if c != col_pontos]
    modificado |= _normalizar_numericos(df_novo, cols_num, corrigir_escala, 60.0)
    return df_novo, modificado


def sanitizar_dados_barras(df: pd.DataFrame, corrigir_escala: bool = False):
    """Normaliza a tabela de Média e Desvio Padrão (correção de escala apenas sob demanda)."""
    df_novo = df.copy()
    if df_novo.empty:
        return df_novo, False

    modificado = _normalizar_ids(df_novo, "Mes", "Mês ") if "Mes" in df_novo.columns else False
    cols_num = ["Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
    modificado |= _normalizar_numericos(df_novo, cols_num, corrigir_escala, 100.0)
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
    df_novo = df.copy()
    if df_novo.empty:
        return df_novo, False

    col_ponto = "Ponto" if "Ponto" in df_novo.columns else df_novo.columns[0]
    modificado = _normalizar_ids(df_novo, col_ponto, "P")
    _normalizar_numericos(df_novo, ["X", "Y"], False, 0.0)
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
        "ss_xx": ss_xx,
        "media_x": x_mean,
        "desvio_x": float(np.std(x, ddof=1)) if n > 1 else 0.0,
        "min_x": float(np.min(x)),
        "max_x": float(np.max(x)),
        "media_y": y_mean,
        "desvio_y": float(np.std(y, ddof=1)) if n > 1 else 0.0,
        "min_y": float(np.min(y)),
        "max_y": float(np.max(y)),
    }



# Quantis bicaudais exatos t(0,975; gl) para gl = 1..30
_T_975 = [
    12.7062, 4.3027, 3.1824, 2.7764, 2.5706, 2.4469, 2.3646, 2.3060, 2.2622, 2.2281,
    2.2010, 2.1788, 2.1604, 2.1448, 2.1314, 2.1199, 2.1098, 2.1009, 2.0930, 2.0860,
    2.0796, 2.0739, 2.0687, 2.0639, 2.0595, 2.0555, 2.0518, 2.0484, 2.0452, 2.0423,
]


def quantil_t_975(graus_liberdade: int) -> float:
    """
    Quantil 97,5% da distribuição t de Student (base do IC 95% bicaudal), sem depender do SciPy.
    gl <= 30 usa a tabela exata; acima disso a expansão de Cornish-Fisher (erro < 1e-4).
    """
    gl = int(graus_liberdade)
    if gl < 1:
        raise ValueError("graus_liberdade deve ser >= 1")
    if gl <= len(_T_975):
        return _T_975[gl - 1]
    z = 1.959963984540054
    return float(
        z
        + (z ** 3 + z) / (4 * gl)
        + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * gl ** 2)
        + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * gl ** 3)
    )


def calcular_banda_regressao(reg: dict, x_vals, nivel: float = 0.95, predicao: bool = False):
    """
    Banda em torno da reta de regressão para os pontos x_vals:
    - predicao=False: intervalo de confiança da média ajustada  ŷ ± t·Se·√(1/n + (x−x̄)²/Sxx)
    - predicao=True:  intervalo de predição de uma nova medição ŷ ± t·Se·√(1 + 1/n + (x−x̄)²/Sxx)
    Retorna (inferior, superior) ou None se n <= 2 (sem graus de liberdade para Se).
    """
    if abs(nivel - 0.95) > 1e-9:
        raise ValueError("Apenas o nível de 95% é suportado.")
    if not reg or reg.get("n", 0) <= 2 or reg.get("ss_xx", 0) <= 0:
        return None
    x = np.asarray(x_vals, dtype=float)
    n = reg["n"]
    t = quantil_t_975(n - 2)
    termo = 1.0 / n + (x - reg["media_x"]) ** 2 / reg["ss_xx"]
    if predicao:
        termo = termo + 1.0
    meia_largura = t * reg["se"] * np.sqrt(termo)
    y_hat = reg["slope"] * x + reg["intercept"]
    return y_hat - meia_largura, y_hat + meia_largura


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
