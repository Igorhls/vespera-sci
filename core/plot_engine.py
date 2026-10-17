"""
Motor de renderização gráfica científica em Matplotlib para o Vespera Sci.
Suporta renderização direta em Figure/Axes (tanto para exportação quanto para FigureCanvasQTAgg)
e habilita legenda arrastável com o mouse (leg.set_draggable(True)).
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from core.sanitizer import formatar_numero_ptbr


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

    if ticks_config.get("minor_ticks", True):
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
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
        ax.yaxis.set_major_locator(ticker.MultipleLocator(2))

    if exibir_grade:
        ax.grid(True, color="#e0e0e0", linestyle="--", linewidth=0.6)
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
):
    """
    Renderiza o Gráfico de Barras Agrupadas (Média e Desvio Padrão: Bosque vs Estacionamento)
    no padrão OriginLab Pro com suporte a legenda arrastável.
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
        largura_barra = largura_grupo / n_series
        offsets = np.linspace(
            -largura_grupo / 2.0 + largura_barra / 2.0,
            largura_grupo / 2.0 - largura_barra / 2.0,
            n_series,
        )

        for idx_s, (col_name, label_leg) in enumerate(series_plot):
            valores = pd.to_numeric(df[col_name], errors="coerce").fillna(0.0).tolist()
            posicoes_x = x_indices + offsets[idx_s]
            cor_b = cores_barras.get(col_name, "#cccccc")

            barras = ax.bar(
                posicoes_x,
                valores,
                width=largura_barra,
                label=label_leg,
                color=cor_b,
                edgecolor="#707070",
                linewidth=0.75,
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

    intervalo_y = pad_max - pad_min
    passo_maior_y = 5.0 if intervalo_y >= 15.0 else 2.0
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_maior_y))

    if ticks_config.get("minor_ticks", True):
        if len(x_indices) > 0:
            ax.xaxis.set_minor_locator(ticker.FixedLocator(np.arange(-0.5, len(x_indices) + 0.5, 1.0)))
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

    if exibir_grade:
        ax.grid(True, axis="y", color="#e0e0e0", linestyle="--", linewidth=0.6, zorder=0)
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
