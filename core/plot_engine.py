"""
Motor de renderização gráfica científica em Matplotlib para o Vespera Sci.
Suporta renderização direta em Figure/Axes (tanto para exportação quanto para FigureCanvasQTAgg)
e habilita legenda arrastável com o mouse (leg.set_draggable(True)).
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from core.sanitizer import calcular_regressao_linear, formatar_numero_ptbr


def configurar_fonte_matplotlib(fonte_nome: str):
    """Configura a família tipográfica do Matplotlib."""
    if "Times" in fonte_nome:
        plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif", "serif"]
        plt.rcParams["font.family"] = "serif"
    elif "Cambria" in fonte_nome:
        plt.rcParams["font.serif"] = ["Cambria", "Georgia", "serif"]
        plt.rcParams["font.family"] = "serif"
    elif "Garamond" in fonte_nome:
        plt.rcParams["font.serif"] = ["Garamond", "Georgia", "serif"]
        plt.rcParams["font.family"] = "serif"
    else:
        plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"]
        plt.rcParams["font.family"] = "sans-serif"


def calcular_passo_ticks_y(pad_min: float, pad_max: float, intervalo_config: float = 0.0) -> float:
    """Calcula o passo dos ticks principais do eixo Y.

    Se intervalo_config > 0, respeita a escolha manual do usuário.
    Se intervalo_config <= 0 (automático), escolhe um passo padrão científico (1, 2, 5, 10, 20...)
    para gerar entre 4 e 7 divisões limpas, evitando aglomeração de números.
    """
    if intervalo_config and float(intervalo_config) > 0.0:
        return float(intervalo_config)

    delta = abs(pad_max - pad_min)
    if delta <= 0:
        return 1.0

    passo_bruto = delta / 6.0
    ordem = 10.0 ** np.floor(np.log10(passo_bruto))
    fracao = passo_bruto / ordem
    if fracao <= 1.5:
        fator = 1.0
    elif fracao <= 3.5:
        fator = 2.0
    elif fracao <= 7.5:
        fator = 5.0
    else:
        fator = 10.0
    return float(fator * ordem)



def renderizar_grafico_linhas(
    df: pd.DataFrame,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_y: float,
    max_y: float,
    series_ativas: list,
    cores_periodos: dict,
    estilos_linhas: dict,
    fonte_nome: str,
    tamanho_fonte: float,
    espessura_linha: float,
    com_marcadores: bool,
    bordas_config: dict,
    ticks_config: dict,
    legenda_config: dict,
    exibir_grade: bool,
    fig=None,
    marcadores_map: dict = None,
    rotulos_legenda: dict = None,
    tamanho_marcador: float = 6.0,
):
    """
    Renderiza o gráfico de linhas (Pontos P1..Pn) com controle milimétrico de tipografia,
    cores, séries visíveis, bordas do quadro e legenda arrastável.
    """
    configurar_fonte_matplotlib(fonte_nome)

    if fig is None:
        fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    else:
        fig.clear()
        ax = fig.add_subplot(111)

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    pontos = df["Pontos"].astype(str).tolist()
    x_indices = np.arange(len(pontos))

    if marcadores_map is None:
        marcadores_map = {"Manha": "o", "Tarde": "s", "Noite": "^"}

    for periodo in ["Manha", "Tarde", "Noite"]:
        if periodo in df.columns and periodo in series_ativas:
            m = marcadores_map.get(periodo) if com_marcadores else None
            if m == "None" or not m:
                m = None
            ls = estilos_linhas.get(periodo, "-")
            cor = cores_periodos.get(periodo, "#000000")
            lbl = rotulos_legenda.get(periodo, periodo) if rotulos_legenda else periodo

            ax.plot(
                x_indices,
                pd.to_numeric(df[periodo], errors="coerce"),
                label=lbl,
                color=cor,
                linestyle=ls,
                linewidth=espessura_linha,
                marker=m,
                markersize=tamanho_marcador,
                markeredgecolor=cor,
                markerfacecolor="white" if com_marcadores and "Monocromático" in str(cores_periodos) else cor,
            )

    ax.set_xticks(x_indices)
    ax.set_xticklabels(pontos, fontsize=tamanho_fonte - 0.5)

    todas_temps = []
    for col in ["Manha", "Tarde", "Noite"]:
        if col in df.columns and col in series_ativas:
            todas_temps.extend(pd.to_numeric(df[col], errors="coerce").dropna().tolist())

    if todas_temps:
        real_min = min(todas_temps)
        real_max = max(todas_temps)
        pad_min = (int(real_min // 2) * 2) if min_y is None else float(min_y)
        pad_max = (int(np.ceil(real_max / 2)) * 2) if max_y is None else float(max_y)
        if pad_max <= pad_min:
            pad_max = pad_min + 2.0
        ax.set_ylim(pad_min, pad_max)
    elif min_y is not None and max_y is not None:
        ax.set_ylim(float(min_y), max(float(max_y), float(min_y) + 2.0))

    if len(x_indices) > 0:
        ax.set_xlim(-0.55, len(x_indices) - 0.45)

    cor_borda = bordas_config.get("cor", "black")
    esp_borda = bordas_config.get("espessura", 1.15)

    ax.spines["top"].set_visible(bordas_config.get("topo", True))
    ax.spines["right"].set_visible(bordas_config.get("direita", True))
    ax.spines["bottom"].set_visible(bordas_config.get("baixo", True))
    ax.spines["left"].set_visible(bordas_config.get("esquerda", True))

    for s_name in ["top", "right", "bottom", "left"]:
        ax.spines[s_name].set_color(cor_borda)
        ax.spines[s_name].set_linewidth(esp_borda)

    direcao_t = ticks_config.get("direcao", "in")
    ticks_topo = ticks_config.get("topo", True) and bordas_config.get("topo", True)
    ticks_dir = ticks_config.get("direita", True) and bordas_config.get("direita", True)
    ticks_baixo = ticks_config.get("baixo", True) and bordas_config.get("baixo", True)
    ticks_esq = ticks_config.get("esquerda", True) and bordas_config.get("esquerda", True)

    ax.tick_params(
        which="major",
        direction=direcao_t,
        top=ticks_topo,
        right=ticks_dir,
        bottom=ticks_baixo,
        left=ticks_esq,
        length=5.5,
        width=1.1,
        color=cor_borda,
        labelsize=tamanho_fonte - 0.5,
    )

    passo_y = calcular_passo_ticks_y(pad_min, pad_max, ticks_config.get("intervalo_y", 0.0))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_y))

    if ticks_config.get("minor_ticks", True):
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        subdivisoes = 5 if (passo_y >= 5.0 and passo_y % 5 == 0) else 2
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(subdivisoes))
        ax.tick_params(
            which="minor",
            direction=direcao_t,
            top=ticks_topo,
            right=ticks_dir,
            bottom=ticks_baixo,
            left=ticks_esq,
            length=3.2,
            width=0.8,
            color=cor_borda,
        )
    else:
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.yaxis.set_minor_locator(ticker.NullLocator())

    ax.set_axisbelow(True)
    if exibir_grade:
        ax.grid(
            True,
            which="major",
            axis="both",
            color="#cbd5e1",
            linestyle="--",
            linewidth=0.85,
            alpha=0.85,
            zorder=0,
        )
    else:
        ax.grid(False)

    ax.set_xlabel(rotulo_x, fontsize=tamanho_fonte, color="black", labelpad=8)
    ax.set_ylabel(rotulo_y, fontsize=tamanho_fonte, color="black", labelpad=8)

    if titulo_grafico and titulo_grafico.strip():
        pad_val = 12 if bordas_config.get("topo", True) else 22
        ax.set_title(titulo_grafico, fontsize=tamanho_fonte + 1.5, color="black", pad=pad_val, fontweight="normal")

    if legenda_config.get("exibir", True) and len(series_ativas) > 0:
        pos_x = legenda_config.get("pos_x", 0.98)
        pos_y = legenda_config.get("pos_y", 0.98)
        loc_ancora = legenda_config.get("loc", "upper right")
        ncol_leg = len(series_ativas) if legenda_config.get("orientacao") == "Horizontal" else 1
        moldura_leg = legenda_config.get("moldura", True)

        leg = ax.legend(
            loc=loc_ancora,
            bbox_to_anchor=(pos_x, pos_y),
            ncol=ncol_leg,
            frameon=moldura_leg,
            edgecolor="black" if moldura_leg else "none",
            facecolor="white",
            framealpha=1.0,
            fontsize=tamanho_fonte - 1.5,
            handlelength=2.4,
            handletextpad=0.6,
            borderpad=0.55,
            columnspacing=1.5,
        )
        if moldura_leg:
            leg.get_frame().set_linewidth(1.0)
        try:
            leg.set_draggable(True)
        except Exception:
            pass

    fig.tight_layout()
    return fig


def calcular_posicoes_barras(
    n_series: int,
    largura_grupo: float = 0.70,
    espaco_subgrupos: float = 0.35,
    espaco_barras: float = 0.0,
):
    """
    Calcula a largura individual de cada barra e os offsets em relação ao centro do cluster.

    Se n_series == 4, divide em 2 subgrupos (0,1) e (2,3) com espaco_subgrupos entre eles.
    Se n_series é par e >= 4, insere o espaco_subgrupos no ponto central (n_series // 2).
    """
    if n_series <= 0:
        return 0.1, []

    ponto_subgrupo = (n_series // 2) if (n_series >= 4 and n_series % 2 == 0) else None

    num_gaps_barras = n_series - 1
    num_gaps_sub = 1 if ponto_subgrupo is not None and espaco_subgrupos > 0 else 0
    if num_gaps_sub > 0:
        num_gaps_barras -= 1

    fator_total = (
        float(n_series)
        + float(num_gaps_barras) * float(espaco_barras)
        + float(num_gaps_sub) * float(espaco_subgrupos + espaco_barras)
    )
    if fator_total <= 0:
        fator_total = float(n_series)

    largura_barra = float(largura_grupo) / fator_total
    gap_b = float(espaco_barras) * largura_barra
    gap_s = float(espaco_subgrupos) * largura_barra

    centers = []
    current_edge = 0.0
    for i in range(n_series):
        center_i = current_edge + 0.5 * largura_barra
        centers.append(center_i)
        current_edge += largura_barra
        if i < n_series - 1:
            if ponto_subgrupo is not None and (i + 1) == ponto_subgrupo:
                current_edge += gap_b + gap_s
            else:
                current_edge += gap_b

    total_w = current_edge
    midpoint = total_w / 2.0
    offsets = [c - midpoint for c in centers]
    return largura_barra, offsets


def renderizar_grafico_barras(
    df: pd.DataFrame,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_y: float,
    max_y: float,
    series_barras_ativas: list,
    cores_barras: dict,
    rotulos_legenda: dict,
    fonte_nome: str,
    tamanho_fonte: float,
    exibir_valores: bool,
    formato_decimais: str,
    negrito_valores: bool,
    largura_grupo: float,
    bordas_config: dict,
    ticks_config: dict,
    legenda_config: dict,
    exibir_grade: bool,
    fig=None,
    hachuras_barras: dict = None,
    espaco_subgrupos: float = 0.35,
    espaco_barras: float = 0.0,
):
    """
    Renderiza o Gráfico de Barras Agrupadas (Média e Desvio Padrão: Bosque vs Estacionamento)
    no padrão OriginLab Pro com suporte a padrões de hachura (hatches), espaçamento de subgrupos e legenda arrastável.
    """
    configurar_fonte_matplotlib(fonte_nome)

    if fig is None:
        fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=200)
    else:
        fig.clear()
        ax = fig.add_subplot(111)

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    meses = df["Mes"].astype(str).tolist()
    x_indices = np.arange(len(meses))

    todas_series = [
        ("Bosque", rotulos_legenda.get("Bosque", "Bosque")),
        ("Desvio_Bosque", rotulos_legenda.get("Desvio_Bosque", "Desvio/p")),
        ("Estacionamento", rotulos_legenda.get("Estacionamento", "Estacionamento")),
        ("Desvio_Estacionamento", rotulos_legenda.get("Desvio_Estacionamento", "Desvio/p")),
    ]
    series_plot = [(col, lab) for col, lab in todas_series if col in series_barras_ativas and col in df.columns]

    n_series = len(series_plot)
    if n_series > 0 and len(x_indices) > 0:
        largura_barra, offsets = calcular_posicoes_barras(
            n_series=n_series,
            largura_grupo=largura_grupo,
            espaco_subgrupos=espaco_subgrupos,
            espaco_barras=espaco_barras,
        )

        for idx_s, (col_name, label_leg) in enumerate(series_plot):
            valores = pd.to_numeric(df[col_name], errors="coerce").fillna(0.0).tolist()
            posicoes_x = x_indices + offsets[idx_s]
            cor_b = cores_barras.get(col_name, "#cccccc")
            hatch_b = hachuras_barras.get(col_name) if hachuras_barras else None

            barras = ax.bar(
                posicoes_x,
                valores,
                width=largura_barra,
                label=label_leg,
                color=cor_b,
                edgecolor="black",
                linewidth=0.9,
                hatch=hatch_b,
                zorder=3,
            )

            if exibir_valores:
                for rect, val_orig in zip(barras, df[col_name]):
                    if pd.notnull(val_orig):
                        altura = rect.get_height()
                        txt_val = formatar_numero_ptbr(val_orig, formato_decimais)
                        ax.annotate(
                            txt_val,
                            xy=(rect.get_x() + rect.get_width() / 2.0, altura),
                            xytext=(0, 2.5),
                            textcoords="offset points",
                            ha="center",
                            va="bottom",
                            fontsize=tamanho_fonte - 1.2,
                            fontweight="bold" if negrito_valores else "normal",
                            color="black",
                            zorder=4,
                        )

    ax.set_xticks(x_indices)
    ax.set_xticklabels(meses, fontsize=tamanho_fonte - 0.5)

    pad_min = 0.0 if min_y is None else float(min_y)
    pad_max = 35.0 if max_y is None else float(max_y)
    if pad_max <= pad_min:
        pad_max = pad_min + 10.0
    ax.set_ylim(pad_min, pad_max)

    if len(x_indices) > 0:
        ax.set_xlim(-0.5, len(x_indices) - 0.5)

    cor_borda = bordas_config.get("cor", "black")
    esp_borda = bordas_config.get("espessura", 1.0)

    ax.spines["top"].set_visible(bordas_config.get("topo", True))
    ax.spines["right"].set_visible(bordas_config.get("direita", True))
    ax.spines["bottom"].set_visible(bordas_config.get("baixo", True))
    ax.spines["left"].set_visible(bordas_config.get("esquerda", True))

    for s_name in ["top", "right", "bottom", "left"]:
        ax.spines[s_name].set_color(cor_borda)
        ax.spines[s_name].set_linewidth(esp_borda)

    direcao_t = ticks_config.get("direcao", "out")
    ticks_topo = ticks_config.get("topo", False) and bordas_config.get("topo", True)
    ticks_dir = ticks_config.get("direita", False) and bordas_config.get("direita", True)
    ticks_baixo = ticks_config.get("baixo", True) and bordas_config.get("baixo", True)
    ticks_esq = ticks_config.get("esquerda", True) and bordas_config.get("esquerda", True)

    ax.tick_params(
        which="major",
        direction=direcao_t,
        top=ticks_topo,
        right=ticks_dir,
        bottom=ticks_baixo,
        left=ticks_esq,
        length=5.0,
        width=1.0,
        color=cor_borda,
        labelsize=tamanho_fonte - 0.5,
    )

    passo_maior_y = calcular_passo_ticks_y(pad_min, pad_max, ticks_config.get("intervalo_y", 0.0))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_maior_y))

    if ticks_config.get("minor_ticks", True):
        if len(x_indices) > 0:
            ax.xaxis.set_minor_locator(ticker.FixedLocator(np.arange(-0.5, len(x_indices) + 0.5, 1.0)))
        subdivisoes = 5 if (passo_maior_y >= 5.0 and passo_maior_y % 5 == 0) else 2
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(subdivisoes))
        ax.tick_params(
            which="minor",
            direction=direcao_t,
            top=ticks_topo,
            right=ticks_dir,
            bottom=ticks_baixo,
            left=ticks_esq,
            length=2.8,
            width=0.8,
            color=cor_borda,
        )
    else:
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.yaxis.set_minor_locator(ticker.NullLocator())

    ax.set_axisbelow(True)
    if exibir_grade:
        ax.grid(
            True,
            which="major",
            axis="y",
            color="#cbd5e1",
            linestyle="--",
            linewidth=0.85,
            alpha=0.85,
            zorder=0,
        )
    else:
        ax.grid(False)

    ax.set_xlabel(rotulo_x, fontsize=tamanho_fonte + 0.5, color="black", labelpad=8)
    ax.set_ylabel(rotulo_y, fontsize=tamanho_fonte, color="black", labelpad=8)

    if titulo_grafico and titulo_grafico.strip():
        pad_val = 12 if bordas_config.get("topo", True) else 22
        ax.set_title(titulo_grafico, fontsize=tamanho_fonte + 1.5, color="black", pad=pad_val, fontweight="normal")

    if legenda_config.get("exibir", True) and n_series > 0:
        pos_x = legenda_config.get("pos_x", 0.98)
        pos_y = legenda_config.get("pos_y", 0.98)
        loc_ancora = legenda_config.get("loc", "upper right")
        ncol_leg = n_series if legenda_config.get("orientacao") == "Horizontal" else 1
        moldura_leg = legenda_config.get("moldura", True)

        leg = ax.legend(
            loc=loc_ancora,
            bbox_to_anchor=(pos_x, pos_y),
            ncol=ncol_leg,
            frameon=moldura_leg,
            edgecolor="black" if moldura_leg else "none",
            facecolor="white",
            framealpha=1.0,
            fontsize=tamanho_fonte - 2.0,
            handlelength=1.8,
            handleheight=1.1,
            handletextpad=0.5,
            borderpad=0.45,
            labelspacing=0.35,
            columnspacing=1.2,
        )
        if moldura_leg:
            leg.get_frame().set_linewidth(0.9)
            leg.set_zorder(10)
        try:
            leg.set_draggable(True)
        except Exception:
            pass

    fig.tight_layout()
    return fig


def renderizar_grafico_dispersao(
    df: pd.DataFrame,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    fonte_nome: str,
    tamanho_fonte: float,
    cor_pontos: str,
    cor_borda_pontos: str,
    marcador_pontos: str,
    tamanho_pontos: float,
    exibir_pontos: bool,
    exibir_reta: bool,
    cor_reta: str,
    estilo_reta: str,
    espessura_reta: float,
    exibir_r2: bool,
    exibir_equacao: bool,
    exibir_banda: bool,
    exibir_rotulos_pontos: bool,
    posicao_r2: str,
    bordas_config: dict,
    ticks_config: dict,
    legenda_config: dict,
    exibir_grade: bool,
    fig=None,
    intervalo_ticks_x: float = 0.0,
    intervalo_ticks_y: float = 0.0,
):
    """
    Renderiza o Gráfico de Dispersão com Regressão Linear e indicador R²
    no padrão acadêmico OriginLab / ABNT.
    """
    configurar_fonte_matplotlib(fonte_nome)

    if fig is None:
        fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=200)
    else:
        fig.clear()
        ax = fig.add_subplot(111)

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Extrai colunas X e Y
    col_x = "X" if "X" in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    col_y = "Y" if "Y" in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[-1])
    col_ponto = "Ponto" if "Ponto" in df.columns else df.columns[0]

    s_x = pd.to_numeric(df[col_x], errors="coerce")
    s_y = pd.to_numeric(df[col_y], errors="coerce")
    mask = (~s_x.isna()) & (~s_y.isna())
    x_valid = s_x[mask].to_numpy(dtype=float)
    y_valid = s_y[mask].to_numpy(dtype=float)
    pontos_valid = df.loc[mask, col_ponto].astype(str).tolist() if col_ponto in df.columns else []

    # Cálculos de limites automáticos se não fornecidos
    if len(x_valid) > 0:
        real_min_x, real_max_x = float(np.min(x_valid)), float(np.max(x_valid))
        delta_x = real_max_x - real_min_x or 1.0
        pad_min_x = (real_min_x - 0.05 * delta_x) if min_x is None else float(min_x)
        pad_max_x = (real_max_x + 0.05 * delta_x) if max_x is None else float(max_x)
    else:
        pad_min_x = 0.0 if min_x is None else float(min_x)
        pad_max_x = 10.0 if max_x is None else float(max_x)

    if len(y_valid) > 0:
        real_min_y, real_max_y = float(np.min(y_valid)), float(np.max(y_valid))
        delta_y = real_max_y - real_min_y or 1.0
        pad_min_y = (real_min_y - 0.05 * delta_y) if min_y is None else float(min_y)
        pad_max_y = (real_max_y + 0.05 * delta_y) if max_y is None else float(max_y)
    else:
        pad_min_y = 0.0 if min_y is None else float(min_y)
        pad_max_y = 10.0 if max_y is None else float(max_y)

    if pad_max_x <= pad_min_x:
        pad_max_x = pad_min_x + 1.0
    if pad_max_y <= pad_min_y:
        pad_max_y = pad_min_y + 1.0

    ax.set_xlim(pad_min_x, pad_max_x)
    ax.set_ylim(pad_min_y, pad_max_y)

    # 1. Plot dos Pontos de Dispersão
    m_sym = marcador_pontos if marcador_pontos and marcador_pontos != "None" else "o"
    tamanho_scatter = (float(tamanho_pontos) * 2.8) ** 2 / 10.0

    if exibir_pontos and len(x_valid) > 0:
        ax.scatter(
            x_valid,
            y_valid,
            color=cor_pontos,
            edgecolor=cor_borda_pontos or cor_pontos,
            s=tamanho_scatter,
            marker=m_sym,
            linewidth=1.0,
            zorder=4,
            label="Medições",
        )

        if exibir_rotulos_pontos and len(pontos_valid) == len(x_valid):
            for px, py, p_name in zip(x_valid, y_valid, pontos_valid):
                ax.annotate(
                    p_name,
                    xy=(px, py),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=tamanho_fonte - 2.5,
                    color="#334155",
                    zorder=5,
                )

    # 2. Regressão Linear Simples e R²
    reg = calcular_regressao_linear(x_valid, y_valid)
    if reg and len(x_valid) >= 2:
        slope = reg["slope"]
        intercept = reg["intercept"]
        r2 = reg["r2"]
        se = reg["se"]

        x_line = np.linspace(np.min(x_valid), np.max(x_valid), 100)
        y_line = slope * x_line + intercept

        if exibir_reta:
            ax.plot(
                x_line,
                y_line,
                color=cor_reta,
                linestyle=estilo_reta or ":",
                linewidth=float(espessura_reta or 1.8),
                zorder=3,
                label=f"Tendência (R² = {reg['r2_formatado']})",
            )

            if exibir_banda and se > 0:
                ax.fill_between(
                    x_line,
                    y_line - 1.96 * se,
                    y_line + 1.96 * se,
                    color=cor_reta,
                    alpha=0.15,
                    zorder=2,
                    label="IC 95%",
                )

        # 3. Rótulo de R² e Equação
        texto_linhas = []
        if exibir_equacao:
            texto_linhas.append(reg["equacao"])
        if exibir_r2:
            texto_linhas.append(f"R² = {reg['r2_formatado']}")

        if texto_linhas:
            full_txt = "\n".join(texto_linhas)
            if "Superior Direito" in posicao_r2:
                ax.text(
                    0.96,
                    0.94,
                    full_txt,
                    transform=ax.transAxes,
                    fontsize=tamanho_fonte - 0.5,
                    color="#222222",
                    ha="right",
                    va="top",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cbd5e1", alpha=0.9),
                    zorder=6,
                )
            elif "Superior Esquerdo" in posicao_r2:
                ax.text(
                    0.05,
                    0.94,
                    full_txt,
                    transform=ax.transAxes,
                    fontsize=tamanho_fonte - 0.5,
                    color="#222222",
                    ha="left",
                    va="top",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cbd5e1", alpha=0.9),
                    zorder=6,
                )
            elif "Inferior Direito" in posicao_r2:
                ax.text(
                    0.96,
                    0.06,
                    full_txt,
                    transform=ax.transAxes,
                    fontsize=tamanho_fonte - 0.5,
                    color="#222222",
                    ha="right",
                    va="bottom",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cbd5e1", alpha=0.9),
                    zorder=6,
                )
            else:
                # Padrão: Junto à reta (próximo ao topo da reta)
                x_pos = np.min(x_valid) + 0.72 * (np.max(x_valid) - np.min(x_valid))
                y_pos = slope * x_pos + intercept + 0.035 * (pad_max_y - pad_min_y)
                ax.text(
                    x_pos,
                    y_pos,
                    full_txt,
                    fontsize=tamanho_fonte - 0.5,
                    color="#222222",
                    ha="center",
                    va="bottom",
                    zorder=6,
                )

    # 4. Configuração de Borda e Spines
    cor_borda = bordas_config.get("cor", "black")
    esp_borda = bordas_config.get("espessura", 1.0)
    for s_name in ["top", "right", "bottom", "left"]:
        ax.spines[s_name].set_visible(bordas_config.get(s_name if s_name != "baixo" else "baixo", True))
        ax.spines[s_name].set_color(cor_borda)
        ax.spines[s_name].set_linewidth(esp_borda)

    # 5. Configuração dos Ticks
    direcao_t = ticks_config.get("direcao", "in")
    ticks_topo = ticks_config.get("topo", True) and bordas_config.get("topo", True)
    ticks_dir = ticks_config.get("direita", True) and bordas_config.get("direita", True)
    ticks_baixo = ticks_config.get("baixo", True) and bordas_config.get("baixo", True)
    ticks_esq = ticks_config.get("esquerda", True) and bordas_config.get("esquerda", True)

    ax.tick_params(
        which="major",
        direction=direcao_t,
        top=ticks_topo,
        right=ticks_dir,
        bottom=ticks_baixo,
        left=ticks_esq,
        length=5.0,
        width=1.0,
        color=cor_borda,
        labelsize=tamanho_fonte - 0.5,
    )

    passo_x = calcular_passo_ticks_y(pad_min_x, pad_max_x, intervalo_ticks_x)
    passo_y = calcular_passo_ticks_y(pad_min_y, pad_max_y, intervalo_ticks_y)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(passo_x))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_y))

    def _fmt_ptbr(val, pos):
        if abs(val - round(val)) < 1e-6:
            return f"{int(round(val))}"
        txt = f"{val:.2f}".rstrip("0").rstrip(".")
        return txt.replace(".", ",")

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(_fmt_ptbr))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_fmt_ptbr))

    if ticks_config.get("minor_ticks", True):
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        ax.tick_params(
            which="minor",
            direction=direcao_t,
            top=ticks_topo,
            right=ticks_dir,
            bottom=ticks_baixo,
            left=ticks_esq,
            length=2.8,
            width=0.8,
            color=cor_borda,
        )
    else:
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.yaxis.set_minor_locator(ticker.NullLocator())

    ax.set_axisbelow(True)
    if exibir_grade:
        ax.grid(
            True,
            which="major",
            axis="both",
            color="#cbd5e1",
            linestyle="--",
            linewidth=0.85,
            alpha=0.85,
            zorder=0,
        )
    else:
        ax.grid(False)

    ax.set_xlabel(rotulo_x, fontsize=tamanho_fonte, color="black", labelpad=8)
    ax.set_ylabel(rotulo_y, fontsize=tamanho_fonte, color="black", labelpad=8)

    if titulo_grafico and titulo_grafico.strip():
        pad_val = 12 if bordas_config.get("topo", True) else 22
        ax.set_title(titulo_grafico, fontsize=tamanho_fonte + 1.5, color="black", pad=pad_val, fontweight="normal")

    if legenda_config.get("exibir", False):
        pos_x = legenda_config.get("pos_x", 0.98)
        pos_y = legenda_config.get("pos_y", 0.98)
        loc_ancora = legenda_config.get("loc", "upper right")
        moldura_leg = legenda_config.get("moldura", True)

        leg = ax.legend(
            loc=loc_ancora,
            bbox_to_anchor=(pos_x, pos_y),
            frameon=moldura_leg,
            edgecolor="black" if moldura_leg else "none",
            facecolor="white",
            framealpha=1.0,
            fontsize=tamanho_fonte - 1.5,
            handlelength=2.0,
            handletextpad=0.5,
            borderpad=0.45,
        )
        if moldura_leg:
            leg.get_frame().set_linewidth(0.9)
            leg.set_zorder(10)
        try:
            leg.set_draggable(True)
        except Exception:
            pass

    fig.tight_layout()
    return fig

