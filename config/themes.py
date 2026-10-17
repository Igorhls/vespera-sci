"""
Paletas de cores científicas, fontes acadêmicas e configuração padrão do Vespera Sci.
"""

# Paletas de cores para Gráfico de Linhas
PALETAS_LINHAS = {
    "OriginLab Pro (Preto, Vermelho, Azul)": {
        "Manha": "#222222",
        "Tarde": "#e74c3c",
        "Noite": "#2980b9",
    },
    "Acadêmico Monocromático (Escala de Cinza)": {
        "Manha": "#111111",
        "Tarde": "#666666",
        "Noite": "#aaaaaa",
    },
    "Nature / Science (Tons Frios & Quentes)": {
        "Manha": "#2c3e50",
        "Tarde": "#d35400",
        "Noite": "#16a085",
    },
    "Excel Clássico": {
        "Manha": "#265b79",
        "Tarde": "#e27641",
        "Noite": "#236532",
    },
}

# Paletas de cores para Gráfico de Barras Agrupadas (Média e Desvio Padrão)
PALETAS_BARRAS = {
    "OriginLab Pastel (Padrão do Modelo)": {
        "Bosque": "#fdc086",
        "Desvio_Bosque": "#8fd194",
        "Estacionamento": "#c2b2d6",
        "Desvio_Estacionamento": "#ffff99",
    },
    "OriginLab Clássico (Cores Vibrantes)": {
        "Bosque": "#f39c12",
        "Desvio_Bosque": "#27ae60",
        "Estacionamento": "#8e44ad",
        "Desvio_Estacionamento": "#f1c40f",
    },
    "Acadêmico Monocromático (Escala de Cinza)": {
        "Bosque": "#333333",
        "Desvio_Bosque": "#777777",
        "Estacionamento": "#aaaaaa",
        "Desvio_Estacionamento": "#dddddd",
    },
    "Nature / Científico (Azul & Verde)": {
        "Bosque": "#2b5c8f",
        "Desvio_Bosque": "#6baed6",
        "Estacionamento": "#31a354",
        "Desvio_Estacionamento": "#a1d99b",
    },
}

FONTES_DISPONIVEIS = [
    "Arial (Científico Internacional)",
    "Times New Roman (Recomendado ABNT)",
    "Cambria (Serifada Elegante)",
    "Garamond (Clássico Acadêmico)",
    "Calibri (Sans-serif Moderna)",
]

POSICOES_LEGENDA = [
    "Superior Direito (Interno)",
    "Superior Esquerdo (Interno)",
    "Inferior Direito (Interno)",
    "Inferior Esquerdo (Interno)",
    "Centro Superior (Externo)",
    "Lateral Direita (Externo)",
    "Personalizada (Arrastar / Coordenadas X/Y)",
]

COORDENADAS_LEGENDA_PRESET = {
    "Superior Direito (Interno)": (0.98, 0.98, "upper right"),
    "Superior Esquerdo (Interno)": (0.02, 0.98, "upper left"),
    "Inferior Direito (Interno)": (0.98, 0.05, "lower right"),
    "Inferior Esquerdo (Interno)": (0.02, 0.05, "lower left"),
    "Centro Superior (Externo)": (0.50, 1.15, "upper center"),
    "Lateral Direita (Externo)": (1.02, 0.50, "center left"),
}

DEFAULT_CONFIG = {
    "rotulo_x": "Pontos",
    "rotulo_y": "Temperatura do ar (°C)",
    "opcao_fonte": "Times New Roman (Recomendado ABNT)",
    "tamanho_fonte": 11.0,
    "opcao_paleta": "OriginLab Pro (Preto, Vermelho, Azul)",
    "cor_manha": "#222222",
    "cor_tarde": "#e74c3c",
    "cor_noite": "#2980b9",
    "opcao_paleta_barras": "OriginLab Pastel (Padrão do Modelo)",
    "cor_bosque": "#fdc086",
    "cor_desvio_bosque": "#8fd194",
    "cor_estacionamento": "#c2b2d6",
    "cor_desvio_estacionamento": "#ffff99",
    "rotulo_s1": "Bosque",
    "rotulo_s2": "Desvio/p",
    "rotulo_s3": "Estacionamento",
    "rotulo_s4": "Desvio/p",
    "exibir_valores_barras": True,
    "formato_decimais_barras": "Automático (ex: 27,32 | 2,3)",
    "negrito_valores_barras": True,
    "largura_grupo_barras": 0.68,
    "espessura_linha": 1.2,
    "modo_estilo_linhas": "Opção 1: Linha + Símbolo (Line + Symbol)",
    "tamanho_marcador": 6.0,
    "rotulos_descritivos_legenda": True,
    "traco_manha": "-",
    "traco_tarde": "-",
    "traco_noite": "-",
    "marcador_manha": "o",
    "marcador_tarde": "s",
    "marcador_noite": "^",
    "com_marcadores": True,
    "exibir_grade": True,
    "com_linhas_distintas": False,
    "show_manha": True,
    "show_tarde": True,
    "show_noite": True,
    "show_bosque": True,
    "show_desvio_bosque": True,
    "show_estacionamento": True,
    "show_desvio_estacionamento": True,
    "exibir_legenda": True,
    "moldura_legenda": True,
    "orientacao_leg": "Vertical (Empilhados)",
    "posicao_preset": "Superior Direito (Interno)",
    "leg_x": 0.98,
    "leg_y": 0.98,
    "borda_top": True,
    "borda_bottom": True,
    "borda_left": True,
    "borda_right": True,
    "ticks_topo": True,
    "ticks_dir": True,
    "ticks_baixo": True,
    "ticks_esq": True,
    "direcao_ticks": "Para dentro (in)",
    "minor_ticks": True,
    "cor_moldura": "#000000",
    "esp_moldura": 1.15,
}

MODOS_ESTILO_LINHAS = [
    "Opção 1: Linha + Símbolo (Line + Symbol)",
    "Opção 2: Estilos de Traçado (Dash Type)",
    "Linhas Contínuas Padrão",
    "Personalizado (Avançado)",
]

MAPA_SIMBOLOS = {
    "Nenhum": "None",
    "Bolinha / Círculo (●)": "o",
    "Quadrado (■)": "s",
    "Triângulo (▲)": "^",
    "Losango (◆)": "D",
    "Estrela (★)": "*",
}

MAPA_TRACOS = {
    "Contínua (———)": "-",
    "Tracejada (- - -)": "--",
    "Pontilhada (······)": ":",
    "Traço-Ponto (— · —)": "-.",
}
