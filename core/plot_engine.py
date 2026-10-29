"""
Motor de renderização gráfica científica em Matplotlib para o Vespera Sci.
Suporta renderização direta em Figure/Axes (tanto para exportação quanto para FigureCanvasQTAgg)
e habilita legenda arrastável com o mouse (leg.set_draggable(True)).
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from core.sanitizer import calcular_banda_regressao, calcular_regressao_linear, formatar_numero_ptbr

LADOS_EIXO = (("top", "topo"), ("right", "direita"), ("bottom", "baixo"), ("left", "esquerda"))
COR_GRADE = "#cbd5e1"


def configurar_fonte_matplotlib(fonte_nome: str):
    """
    Configura a família tipográfica do Matplotlib.
    Os rótulos dos ticks são criados apenas no momento do desenho, por isso a fonte precisa
    estar nos rcParams globais (um rc_context temporário não alcançaria esses textos).
    """
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


def _formatar_tick_ptbr(val, pos=None):
    """Rótulo de tick com vírgula decimal (padrão ABNT / PT-BR)."""
    if abs(val - round(val)) < 1e-6:
        return f"{int(round(val))}"
    txt = f"{val:.4f}".rstrip("0").rstrip(".")
    return txt.replace(".", ",")


# =======================================================================
# Estilo compartilhado entre os quatro tipos de gráfico
# =======================================================================

def _preparar_figura(fig, figsize):
    if fig is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=200)
    else:
        fig.clear()
        ax = fig.add_subplot(111)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax


def _aplicar_bordas(ax, bordas_config: dict, espessura_padrao: float = 1.0):
    cor_borda = bordas_config.get("cor", "black")
    esp_borda = bordas_config.get("espessura", espessura_padrao)
    for lado_mpl, lado_cfg in LADOS_EIXO:
        ax.spines[lado_mpl].set_visible(bordas_config.get(lado_cfg, True))
        ax.spines[lado_mpl].set_color(cor_borda)
        ax.spines[lado_mpl].set_linewidth(esp_borda)
    return cor_borda


def _aplicar_ticks(
    ax,
    ticks_config: dict,
    bordas_config: dict,
    tamanho_fonte: float,
    direcao_padrao: str,
    lados_padrao: dict,
    comprimento_maior: float = 5.0,
    largura_maior: float = 1.0,
    comprimento_menor: float = 2.8,
    locator_menor_x=None,
    locator_menor_y=None,
):
    """Ticks maiores e menores. Um tick só aparece se a borda do mesmo lado estiver visível."""
    cor_borda = bordas_config.get("cor", "black")
    direcao = ticks_config.get("direcao", direcao_padrao)
    lados = {
        lado_mpl: ticks_config.get(lado_cfg, lados_padrao.get(lado_cfg, True)) and bordas_config.get(lado_cfg, True)
        for lado_mpl, lado_cfg in LADOS_EIXO
    }

    ax.tick_params(
        which="major",
        direction=direcao,
        length=comprimento_maior,
        width=largura_maior,
        color=cor_borda,
        labelsize=tamanho_fonte - 0.5,
        **lados,
    )

    if ticks_config.get("minor_ticks", True):
        if locator_menor_x is not None:
            ax.xaxis.set_minor_locator(locator_menor_x)
        if locator_menor_y is not None:
            ax.yaxis.set_minor_locator(locator_menor_y)
        ax.tick_params(
            which="minor",
            direction=direcao,
            length=comprimento_menor,
            width=0.8,
            color=cor_borda,
            **lados,
        )
    else:
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.yaxis.set_minor_locator(ticker.NullLocator())


def _aplicar_grade(ax, exibir_grade: bool, eixo: str):
    ax.set_axisbelow(True)
    if exibir_grade:
        ax.grid(True, which="major", axis=eixo, color=COR_GRADE, linestyle="--", linewidth=0.85, alpha=0.85, zorder=0)
    else:
        ax.grid(False)


def _aplicar_titulo_e_rotulos(ax, titulo, rotulo_x, rotulo_y, tamanho_fonte, bordas_config, delta_fonte_x=0.0):
    ax.set_xlabel(rotulo_x, fontsize=tamanho_fonte + delta_fonte_x, color="black", labelpad=8)
    ax.set_ylabel(rotulo_y, fontsize=tamanho_fonte, color="black", labelpad=8)
    if titulo and titulo.strip():
        pad_val = 12 if bordas_config.get("topo", True) else 22
        ax.set_title(titulo, fontsize=tamanho_fonte + 1.5, color="black", pad=pad_val, fontweight="normal")


def _criar_legenda(
    ax,
    legenda_config: dict,
    ncol: int,
    tamanho_fonte: float,
    reducao_fonte: float = 1.5,
    espessura_moldura: float = 0.9,
    **estilo,
):
    if not ax.get_legend_handles_labels()[0]:
        return None
    moldura = legenda_config.get("moldura", True)
    leg = ax.legend(
        loc=legenda_config.get("loc", "upper right"),
        bbox_to_anchor=(legenda_config.get("pos_x", 0.98), legenda_config.get("pos_y", 0.98)),
        ncol=max(1, ncol) if legenda_config.get("orientacao") == "Horizontal" else 1,
        frameon=moldura,
        edgecolor="black" if moldura else "none",
        facecolor="white",
        framealpha=1.0,
        fontsize=tamanho_fonte - reducao_fonte,
        **estilo,
    )
    if moldura:
        leg.get_frame().set_linewidth(espessura_moldura)
        leg.set_zorder(10)
    try:
        leg.set_draggable(True)
    except Exception:
        pass
    return leg


def _limites_automaticos(valores, min_y, max_y, margem_relativa: float, passo_arredondamento: float = 2.0):
    """
    Limites do eixo Y: usa min_y/max_y do usuário quando fornecidos, senão arredonda os dados
    para múltiplos de passo_arredondamento com a margem pedida. Sempre retorna um par válido.
    """
    if valores:
        vmin, vmax = min(valores), max(valores)
        margem = (vmax - vmin) * margem_relativa if vmax > vmin else passo_arredondamento
        auto_min = np.floor((vmin - margem) / passo_arredondamento) * passo_arredondamento
        auto_max = np.ceil((vmax + margem) / passo_arredondamento) * passo_arredondamento
    else:
        auto_min, auto_max = 0.0, 10.0
    pad_min = float(min_y) if min_y is not None else float(auto_min)
    pad_max = float(max_y) if max_y is not None else float(auto_max)
    if pad_max <= pad_min:
        pad_max = pad_min + passo_arredondamento
    return pad_min, pad_max


# =======================================================================
# Gráfico de Linhas
# =======================================================================

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
    marcadores_vazados: bool = False,
):
    """
    Renderiza o gráfico de linhas (Pontos P1..Pn) com controle milimétrico de tipografia,
    cores, séries visíveis, bordas do quadro e legenda arrastável.
    marcadores_vazados: preenche os símbolos de branco (estilo monocromático para impressão P&B).
    """
    configurar_fonte_matplotlib(fonte_nome)
    fig, ax = _preparar_figura(fig, (7.2, 4.4))

    series_ativas = list(series_ativas or [])
    col_id = "Pontos" if "Pontos" in df.columns else (df.columns[0] if len(df.columns) else None)
    pontos = df[col_id].astype(str).tolist() if col_id is not None and len(df) > 0 else []
    x_indices = np.arange(len(pontos))

    colunas_candidatas = [c for c in df.columns if c != col_id]
    ordem_historica = ["Manha", "Tarde", "Noite"]
    colunas_plot = [c for c in ordem_historica if c in colunas_candidatas] + [c for c in colunas_candidatas if c not in ordem_historica]
    colunas_visiveis = [c for c in colunas_plot if not series_ativas or c in series_ativas]

    PALETA_CORES_PADRAO = ["#222222", "#e74c3c", "#2980b9", "#27ae60", "#8e44ad", "#d35400", "#16a085", "#f39c12", "#34495e"]
    LISTA_MARCADORES_PADRAO = ["o", "s", "^", "D", "v", "<", ">", "p", "*"]

    if marcadores_map is None:
        marcadores_map = {"Manha": "o", "Tarde": "s", "Noite": "^"}

    todos_valores = []
    for idx_col, col_name in enumerate(colunas_plot):
        if col_name not in colunas_visiveis:
            continue

        m = marcadores_map.get(col_name, LISTA_MARCADORES_PADRAO[idx_col % len(LISTA_MARCADORES_PADRAO)]) if com_marcadores else None
        if m == "None" or not m:
            m = None
        ls = estilos_linhas.get(col_name, "-")
        cor = cores_periodos.get(col_name, PALETA_CORES_PADRAO[idx_col % len(PALETA_CORES_PADRAO)])
        lbl = rotulos_legenda.get(col_name, col_name) if rotulos_legenda else col_name

        s_val = pd.to_numeric(df[col_name], errors="coerce")
        todos_valores.extend(s_val.dropna().tolist())
        ax.plot(
            x_indices,
            s_val,
            label=lbl,
            color=cor,
            linestyle=ls,
            linewidth=espessura_linha,
            marker=m,
            markersize=tamanho_marcador,
            markeredgecolor=cor,
            markerfacecolor="white" if (m and marcadores_vazados) else cor,
        )

    if len(x_indices) > 0:
        ax.set_xticks(x_indices)
        ax.set_xticklabels(pontos, fontsize=tamanho_fonte - 0.5)
        ax.set_xlim(-0.55, len(x_indices) - 0.45)

    pad_min, pad_max = _limites_automaticos(todos_valores, min_y, max_y, margem_relativa=0.0)
    ax.set_ylim(pad_min, pad_max)

    _aplicar_bordas(ax, bordas_config, espessura_padrao=1.15)

    passo_y = calcular_passo_ticks_y(pad_min, pad_max, ticks_config.get("intervalo_y", 0.0))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_y))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_formatar_tick_ptbr))
    subdivisoes = 5 if (passo_y >= 5.0 and passo_y % 5 == 0) else 2
    _aplicar_ticks(
        ax, ticks_config, bordas_config, tamanho_fonte,
        direcao_padrao="in",
        lados_padrao={"topo": True, "direita": True, "baixo": True, "esquerda": True},
        comprimento_maior=5.5, largura_maior=1.1, comprimento_menor=3.2,
        locator_menor_x=ticker.AutoMinorLocator(2),
        locator_menor_y=ticker.AutoMinorLocator(subdivisoes),
    )

    _aplicar_grade(ax, exibir_grade, "both")
    _aplicar_titulo_e_rotulos(ax, titulo_grafico, rotulo_x, rotulo_y, tamanho_fonte, bordas_config)

    if legenda_config.get("exibir", True) and colunas_visiveis:
        _criar_legenda(
            ax, legenda_config, len(colunas_visiveis), tamanho_fonte,
            espessura_moldura=1.0, handlelength=2.4, handletextpad=0.6, borderpad=0.55, columnspacing=1.5,
        )

    fig.tight_layout()
    return fig


# =======================================================================
# Gráfico de Barras
# =======================================================================

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


MODO_DESVIO_ERRO = "erro"
MODO_DESVIO_BARRAS = "barras"
PARES_MEDIA_DESVIO = [("Bosque", "Desvio_Bosque"), ("Estacionamento", "Desvio_Estacionamento")]


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
    modo_desvio: str = MODO_DESVIO_ERRO,
):
    """
    Renderiza o Gráfico de Barras Agrupadas (Média e Desvio Padrão: Bosque vs Estacionamento)
    no padrão OriginLab Pro com suporte a padrões de hachura (hatches), espaçamento de subgrupos e legenda arrastável.

    modo_desvio:
    - "erro" (padrão científico): o desvio padrão é desenhado como barra de erro (±DP) sobre a média.
    - "barras": o desvio padrão é desenhado como uma barra própria ao lado da média (layout legado).
    Células vazias não geram barra (em vez de uma barra de altura zero).
    """
    configurar_fonte_matplotlib(fonte_nome)
    fig, ax = _preparar_figura(fig, (7.4, 4.6))

    rotulos_legenda = rotulos_legenda or {}
    hachuras_barras = hachuras_barras or {}
    series_barras_ativas = list(series_barras_ativas or [])
    meses = df["Mes"].astype(str).tolist() if "Mes" in df.columns else [str(i + 1) for i in range(len(df))]
    x_indices = np.arange(len(meses))

    rotulos_padrao = {
        "Bosque": "Bosque",
        "Desvio_Bosque": "Desvio/p",
        "Estacionamento": "Estacionamento",
        "Desvio_Estacionamento": "Desvio/p",
    }

    def _ativa(col):
        return col in series_barras_ativas and col in df.columns

    # Cada item: (coluna da altura, rótulo da legenda, coluna do erro ou None)
    if modo_desvio == MODO_DESVIO_BARRAS:
        series_plot = [
            (col, rotulos_legenda.get(col, rotulos_padrao[col]), None)
            for par in PARES_MEDIA_DESVIO
            for col in par
            if _ativa(col)
        ]
    else:
        series_plot = [
            (media, rotulos_legenda.get(media, rotulos_padrao[media]), desvio if _ativa(desvio) else None)
            for media, desvio in PARES_MEDIA_DESVIO
            if _ativa(media)
        ]

    n_series = len(series_plot)
    topos_barras = []
    if n_series > 0 and len(x_indices) > 0:
        largura_barra, offsets = calcular_posicoes_barras(
            n_series=n_series,
            largura_grupo=largura_grupo,
            espaco_subgrupos=espaco_subgrupos,
            espaco_barras=espaco_barras,
        )

        for idx_s, (col_name, label_leg, col_erro) in enumerate(series_plot):
            valores = pd.to_numeric(df[col_name], errors="coerce").to_numpy(dtype=float)
            erros = (
                pd.to_numeric(df[col_erro], errors="coerce").fillna(0.0).abs().to_numpy(dtype=float)
                if col_erro
                else np.zeros(len(valores))
            )
            validos = ~np.isnan(valores)
            if not validos.any():
                continue

            posicoes_x = (x_indices + offsets[idx_s])[validos]
            alturas = valores[validos]
            erros_validos = erros[validos]

            barras = ax.bar(
                posicoes_x,
                alturas,
                width=largura_barra,
                label=label_leg,
                color=cores_barras.get(col_name, "#cccccc"),
                edgecolor="black",
                linewidth=0.9,
                hatch=hachuras_barras.get(col_name),
                yerr=erros_validos if col_erro else None,
                capsize=4 if col_erro else 0,
                error_kw=dict(elinewidth=1.0, capthick=1.0, ecolor="black", zorder=4),
                zorder=3,
            )
            topos_barras.extend((alturas + erros_validos).tolist())

            if exibir_valores:
                for rect, val, err in zip(barras, alturas, erros_validos):
                    ax.annotate(
                        formatar_numero_ptbr(val, formato_decimais),
                        xy=(rect.get_x() + rect.get_width() / 2.0, rect.get_height() + err),
                        xytext=(0, 2.5),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=tamanho_fonte - 1.2,
                        fontweight="bold" if negrito_valores else "normal",
                        color="black",
                        zorder=5,
                    )

    ax.set_xticks(x_indices)
    ax.set_xticklabels(meses, fontsize=tamanho_fonte - 0.5)

    pad_min = 0.0 if min_y is None else float(min_y)
    if max_y is not None:
        pad_max = float(max_y)
    elif topos_barras:
        pad_max = float(np.ceil(max(topos_barras) * 1.15))
    else:
        pad_max = 35.0
    if pad_max <= pad_min:
        pad_max = pad_min + 10.0
    ax.set_ylim(pad_min, pad_max)

    if len(x_indices) > 0:
        ax.set_xlim(-0.5, len(x_indices) - 0.5)

    _aplicar_bordas(ax, bordas_config)

    passo_maior_y = calcular_passo_ticks_y(pad_min, pad_max, ticks_config.get("intervalo_y", 0.0))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_maior_y))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_formatar_tick_ptbr))
    subdivisoes = 5 if (passo_maior_y >= 5.0 and passo_maior_y % 5 == 0) else 2
    _aplicar_ticks(
        ax, ticks_config, bordas_config, tamanho_fonte,
        direcao_padrao="out",
        lados_padrao={"topo": False, "direita": False, "baixo": True, "esquerda": True},
        locator_menor_x=ticker.FixedLocator(np.arange(-0.5, len(x_indices) + 0.5, 1.0)) if len(x_indices) else None,
        locator_menor_y=ticker.AutoMinorLocator(subdivisoes),
    )

    _aplicar_grade(ax, exibir_grade, "y")
    _aplicar_titulo_e_rotulos(ax, titulo_grafico, rotulo_x, rotulo_y, tamanho_fonte, bordas_config, delta_fonte_x=0.5)

    if legenda_config.get("exibir", True) and n_series > 0:
        _criar_legenda(
            ax, legenda_config, n_series, tamanho_fonte,
            reducao_fonte=2.0, handlelength=1.8, handleheight=1.1, handletextpad=0.5,
            borderpad=0.45, labelspacing=0.35, columnspacing=1.2,
        )

    fig.tight_layout()
    return fig


# =======================================================================
# Gráfico de Dispersão e Regressão
# =======================================================================

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
    A banda opcional é o intervalo de confiança de 95% da reta ajustada (distribuição t, n−2 g.l.).
    """
    configurar_fonte_matplotlib(fonte_nome)
    fig, ax = _preparar_figura(fig, (7.4, 4.6))

    col_x = "X" if "X" in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    col_y = "Y" if "Y" in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[-1])
    col_ponto = "Ponto" if "Ponto" in df.columns else df.columns[0]

    s_x = pd.to_numeric(df[col_x], errors="coerce")
    s_y = pd.to_numeric(df[col_y], errors="coerce")
    mask = (~s_x.isna()) & (~s_y.isna())
    x_valid = s_x[mask].to_numpy(dtype=float)
    y_valid = s_y[mask].to_numpy(dtype=float)
    pontos_valid = df.loc[mask, col_ponto].astype(str).tolist() if col_ponto in df.columns else []

    def _limites(valores, vmin_cfg, vmax_cfg):
        if len(valores) > 0:
            real_min, real_max = float(np.min(valores)), float(np.max(valores))
            delta = real_max - real_min or 1.0
            lo = (real_min - 0.05 * delta) if vmin_cfg is None else float(vmin_cfg)
            hi = (real_max + 0.05 * delta) if vmax_cfg is None else float(vmax_cfg)
        else:
            lo = 0.0 if vmin_cfg is None else float(vmin_cfg)
            hi = 10.0 if vmax_cfg is None else float(vmax_cfg)
        if hi <= lo:
            hi = lo + 1.0
        return lo, hi

    pad_min_x, pad_max_x = _limites(x_valid, min_x, max_x)
    pad_min_y, pad_max_y = _limites(y_valid, min_y, max_y)
    ax.set_xlim(pad_min_x, pad_max_x)
    ax.set_ylim(pad_min_y, pad_max_y)

    # 1. Pontos
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
    if reg:
        slope = reg["slope"]
        intercept = reg["intercept"]

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

            if exibir_banda:
                banda = calcular_banda_regressao(reg, x_line, nivel=0.95)
                if banda is not None:
                    inferior, superior = banda
                    ax.fill_between(
                        x_line,
                        inferior,
                        superior,
                        color=cor_reta,
                        alpha=0.15,
                        zorder=2,
                        label="IC 95% da reta",
                    )

        # 3. Rótulo de R² e Equação
        texto_linhas = []
        if exibir_equacao:
            texto_linhas.append(reg["equacao"])
        if exibir_r2:
            texto_linhas.append(f"R² = {reg['r2_formatado']}")

        if texto_linhas:
            full_txt = "\n".join(texto_linhas)
            caixa = dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=COR_GRADE, alpha=0.9)
            posicoes_fixas = {
                "Superior Direito": (0.96, 0.94, "right", "top"),
                "Superior Esquerdo": (0.05, 0.94, "left", "top"),
                "Inferior Direito": (0.96, 0.06, "right", "bottom"),
            }
            fixa = next((v for k, v in posicoes_fixas.items() if k in posicao_r2), None)
            if fixa:
                px, py, ha, va = fixa
                ax.text(px, py, full_txt, transform=ax.transAxes, fontsize=tamanho_fonte - 0.5,
                        color="#222222", ha=ha, va=va, bbox=caixa, zorder=6)
            else:
                # Padrão: junto à reta (próximo ao topo da reta)
                x_pos = np.min(x_valid) + 0.72 * (np.max(x_valid) - np.min(x_valid))
                y_pos = slope * x_pos + intercept + 0.035 * (pad_max_y - pad_min_y)
                ax.text(x_pos, y_pos, full_txt, fontsize=tamanho_fonte - 0.5,
                        color="#222222", ha="center", va="bottom", zorder=6)

    # 4. Bordas, ticks e grade
    _aplicar_bordas(ax, bordas_config)

    passo_x = calcular_passo_ticks_y(pad_min_x, pad_max_x, intervalo_ticks_x)
    passo_y = calcular_passo_ticks_y(pad_min_y, pad_max_y, intervalo_ticks_y)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(passo_x))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_y))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(_formatar_tick_ptbr))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_formatar_tick_ptbr))
    _aplicar_ticks(
        ax, ticks_config, bordas_config, tamanho_fonte,
        direcao_padrao="in",
        lados_padrao={"topo": True, "direita": True, "baixo": True, "esquerda": True},
        locator_menor_x=ticker.AutoMinorLocator(2),
        locator_menor_y=ticker.AutoMinorLocator(2),
    )

    _aplicar_grade(ax, exibir_grade, "both")
    _aplicar_titulo_e_rotulos(ax, titulo_grafico, rotulo_x, rotulo_y, tamanho_fonte, bordas_config)

    if legenda_config.get("exibir", False):
        legenda_scatter = dict(legenda_config, orientacao="Vertical")
        _criar_legenda(
            ax, legenda_scatter, 1, tamanho_fonte,
            handlelength=2.0, handletextpad=0.5, borderpad=0.45,
        )

    fig.tight_layout()
    return fig


# =======================================================================
# Boxplot
# =======================================================================

COLUNAS_IDENTIFICADORAS = ["ponto", "pontos", "mes", "mês", "id"]


def renderizar_grafico_boxplot(
    df: pd.DataFrame,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_y: float,
    max_y: float,
    series_ativas: list,
    cores_series: dict,
    fonte_nome: str,
    tamanho_fonte: float,
    bordas_config: dict,
    ticks_config: dict,
    legenda_config: dict,
    exibir_grade: bool,
    largura_box: float = 0.5,
    mostrar_medias: bool = True,
    mostrar_outliers: bool = True,
    mostrar_pontos: bool = False,
    intervalo_ticks_y: float = 0.0,
    fig=None,
    series_controladas: list = None,
):
    """
    Renderiza o Gráfico de Boxplot (Distribuição Térmica, Mediana, Quartis Q1/Q3 e Outliers)
    no padrão editorial OriginLab Pro / Nature.

    series_controladas: colunas que possuem um seletor de visibilidade na interface; essas só
    aparecem se estiverem em series_ativas. Colunas sem seletor sempre aparecem.
    Se series_controladas for None, todas as colunas obedecem a series_ativas (vazio = todas).
    """
    configurar_fonte_matplotlib(fonte_nome)
    fig, ax = _preparar_figura(fig, (7.4, 4.6))

    series_ativas = list(series_ativas or [])
    candidatas = [c for c in df.columns if str(c).lower() not in COLUNAS_IDENTIFICADORAS]
    if series_controladas is None:
        cols_plot = [c for c in candidatas if not series_ativas or c in series_ativas]
    else:
        cols_plot = [c for c in candidatas if c not in series_controladas or c in series_ativas]

    dados_plot = []
    labels_plot = []
    todos_valores = []

    for c in cols_plot:
        s = pd.to_numeric(df[c], errors="coerce").dropna().values
        if len(s) > 0:
            dados_plot.append(s)
            labels_plot.append(c)
            todos_valores.extend(s.tolist())

    n_boxes = len(dados_plot)
    if n_boxes > 0:
        posicoes = np.arange(n_boxes)
        bp = ax.boxplot(
            dados_plot,
            positions=posicoes,
            widths=largura_box,
            patch_artist=True,
            showmeans=mostrar_medias,
            showfliers=mostrar_outliers,
            meanprops=dict(marker="D", markeredgecolor="black", markerfacecolor="white", markersize=6),
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(color="black", linewidth=1.1, linestyle="--"),
            capprops=dict(color="black", linewidth=1.2),
            flierprops=dict(marker="o", markerfacecolor="#e74c3c", markeredgecolor="black", markersize=5),
            zorder=3
        )

        for patch, col_name in zip(bp["boxes"], labels_plot):
            patch.set_facecolor(cores_series.get(col_name, "#3b82f6"))
            patch.set_edgecolor("black")
            patch.set_linewidth(1.1)

        if mostrar_pontos:
            # Semente fixa: os pontos não "pulam" a cada redesenho e a figura exportada é reprodutível
            rng = np.random.default_rng(0)
            for idx, s in enumerate(dados_plot):
                jitter = rng.normal(0, 0.04, size=len(s))
                ax.scatter(posicoes[idx] + jitter, s, color="#222222", alpha=0.5, s=20, zorder=4, edgecolor="none")

        ax.set_xticks(posicoes)
        ax.set_xticklabels(labels_plot, fontsize=tamanho_fonte - 0.5)
        ax.set_xlim(-0.6, n_boxes - 0.4)
    else:
        msg = "Nenhuma série selecionada" if candidatas else "Sem dados suficientes para gerar Boxplot"
        ax.text(0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes)

    pad_min, pad_max = _limites_automaticos(todos_valores, min_y, max_y, margem_relativa=0.12)
    ax.set_ylim(pad_min, pad_max)

    passo_y = calcular_passo_ticks_y(pad_min, pad_max, intervalo_ticks_y)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_y))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_formatar_tick_ptbr))

    _aplicar_bordas(ax, bordas_config)
    _aplicar_ticks(
        ax, ticks_config, bordas_config, tamanho_fonte,
        direcao_padrao="out",
        lados_padrao={"topo": False, "direita": False, "baixo": True, "esquerda": True},
        locator_menor_y=ticker.AutoMinorLocator(2),
    )
    # Eixo X categórico: sem ticks menores entre as caixas
    ax.xaxis.set_minor_locator(ticker.NullLocator())

    _aplicar_grade(ax, exibir_grade, "y")
    _aplicar_titulo_e_rotulos(ax, titulo_grafico, rotulo_x, rotulo_y, tamanho_fonte, bordas_config, delta_fonte_x=0.5)

    fig.tight_layout()
    return fig
