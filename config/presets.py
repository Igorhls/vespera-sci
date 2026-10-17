"""
Conjuntos de dados pré-definidos (Presets) para carregamento rápido no Vespera Sci.
"""

import pandas as pd

PRESETS_LINHAS = {
    "Dia 14 de Agosto": {
        "tipo_grafico": "linhas",
        "titulo_dia": "Dia 14 de agosto",
        "titulo_grafico": "DIA 14 DE AGOSTO - BOSQUE",
        "min_y": 24.0,
        "max_y": 33.0,
        "df": pd.DataFrame({
            "Pontos": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"],
            "Manha": [26.2, 26.5, 26.5, 26.9, 27.2, 27.4, 27.1, 27.2, 27.3, 27.6],
            "Tarde": [28.5, 29.0, 29.5, 29.6, 30.4, 29.9, 30.9, 31.4, 30.3, 30.5],
            "Noite": [25.5, 26.1, 26.2, 26.4, 26.9, 26.7, 26.8, 26.9, 27.0, 27.1],
        }),
    },
    "Dia 16 de Agosto": {
        "tipo_grafico": "linhas",
        "titulo_dia": "Dia 16 de agosto",
        "titulo_grafico": "DIA 16 DE AGOSTO - BOSQUE",
        "min_y": 24.0,
        "max_y": 33.0,
        "df": pd.DataFrame({
            "Pontos": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"],
            "Manha": [26.0, 25.3, 25.3, 26.6, 26.2, 25.5, 25.4, 26.2, 26.0, 26.3],
            "Tarde": [28.5, 28.6, 28.9, 31.0, 30.8, 29.5, 30.4, 30.6, 30.0, 29.9],
            "Noite": [25.8, 26.0, 26.1, 26.7, 26.8, 27.0, 27.0, 26.9, 26.6, 27.1],
        }),
    },
    "Dia 19 de Agosto": {
        "tipo_grafico": "linhas",
        "titulo_dia": "Dia 19 de agosto",
        "titulo_grafico": "DIA 19 DE AGOSTO - BOSQUE",
        "min_y": 22.0,
        "max_y": 33.0,
        "df": pd.DataFrame({
            "Pontos": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"],
            "Manha": [24.7, 24.0, 23.4, 23.6, 23.8, 23.6, 23.5, 23.8, 24.2, 24.4],
            "Tarde": [28.2, 28.5, 28.9, 31.5, 31.0, 28.9, 31.0, 31.8, 30.0, 30.6],
            "Noite": [27.1, 25.5, 25.3, 26.7, 26.2, 26.1, 25.8, 27.0, 27.1, 25.6],
        }),
    },
}

PRESETS_BARRAS = {
    "Ta (°C) — Média e Desvio Padrão (Modelo OriginLab da Pesquisa)": {
        "tipo_grafico": "barras",
        "nome_projeto": "Ta (°C) - Média e Desvio Padrão",
        "titulo_dia": "Ta (°C)",
        "titulo_grafico": "",
        "rotulo_x": "",
        "rotulo_y": "Ta (°C)",
        "rotulo_s1": "Bosque",
        "rotulo_s2": "Desvio/p (Bosque)",
        "rotulo_s3": "Estacionamento",
        "rotulo_s4": "Desvio/p (Estacionamento)",
        "min_y": 0.0,
        "max_y": 35.0,
        "df": pd.DataFrame({
            "Mes": ["Agosto", "Dezembro"],
            "Bosque": [27.32, 28.60],
            "Desvio_Bosque": [2.30, 1.42],
            "Estacionamento": [28.50, 29.40],
            "Desvio_Estacionamento": [4.87, 2.19],
        }),
        "config": {
            "opcao_paleta_barras": "OriginLab Hachurado (Verde, Cinza, Laranja //, Branco ..)",
            "cor_bosque": "#2ca02c",
            "cor_desvio_bosque": "#b0b7bd",
            "cor_estacionamento": "#d95f02",
            "cor_desvio_estacionamento": "#ffffff",
            "hachura_bosque": "Nenhum (Sólido)",
            "hachura_desvio_bosque": "Nenhum (Sólido)",
            "hachura_estacionamento": "Diagonal Direita (//)",
            "hachura_desvio_estacionamento": "Pontilhado / Pontos (..)",
            "intervalo_ticks_y": 5.0,
            "direcao_ticks": "Para fora (out)",
            "ticks_topo": False,
            "ticks_dir": False,
            "exibir_grade": True,
            "formato_decimais_barras": "Automático (ex: 27,32 | 2,3)",
            "negrito_valores_barras": False,
        },
    },
    "TA — Média e Desvio Padrão (Agosto e Dezembro)": {
        "tipo_grafico": "barras",
        "nome_projeto": "TA - Média e Desvio Padrão",
        "titulo_dia": "TA",
        "titulo_grafico": "",
        "rotulo_x": "TA",
        "rotulo_y": "Média (%)",
        "rotulo_s1": "Bosque",
        "rotulo_s2": "Desvio/p",
        "rotulo_s3": "Estacionamento",
        "rotulo_s4": "Desvio/p",
        "min_y": 0.0,
        "max_y": 35.0,
        "df": pd.DataFrame({
            "Mes": ["Agosto", "Dezembro"],
            "Bosque": [27.32, 28.60],
            "Desvio_Bosque": [2.30, 1.42],
            "Estacionamento": [28.50, 29.40],
            "Desvio_Estacionamento": [4.87, 2.19],
        }),
    },
}
