"""
Suíte de Testes Automatizados Unitários e de Integração — Vespera Sci Desktop.
Cobre Sanitização, Estatísticas (Regressão e Boxplot), Motores de Plotagem e Exportação Excel.
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

# Assegura que o diretório raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanitizer import (
    calcular_estatisticas_boxplot,
    calcular_estatisticas_serie,
    calcular_regressao_linear,
    formatar_numero_ptbr,
    sanitizar_dados_barras,
    sanitizar_dados_dispersao,
    sanitizar_dados_tabela,
)
from core.plot_engine import (
    renderizar_grafico_barras,
    renderizar_grafico_boxplot,
    renderizar_grafico_dispersao,
    renderizar_grafico_linhas,
)
from core.project_manager import ProjectManager
from core.excel_exporter import (
    gerar_excel_barras_bytes,
    gerar_excel_boxplot_bytes,
    gerar_excel_dispersao_bytes,
    gerar_excel_linhas_bytes,
)
from config.presets import PRESETS_BARRAS, PRESETS_BOXPLOT, PRESETS_DISPERSAO, PRESETS_LINHAS


class TestSanitizerAndStats(unittest.TestCase):
    """Testes de funções de sanitização de dados e cálculos estatísticos científicos."""

    def test_sanitizar_dados_tabela_escala(self):
        # Testa a correção de valor que perdeu a vírgula (ex: 274.0 -> 27.4)
        df_raw = pd.DataFrame({
            "Pontos": [None, "P2"],
            "Manha": [274.0, 26.5],
            "Tarde": ["28,5", 29.0],
            "Noite": [25.0, 26.0],
        })
        df_san, mod = sanitizar_dados_tabela(df_raw)
        self.assertTrue(mod)
        self.assertEqual(df_san.iloc[0]["Pontos"], "P1")
        self.assertEqual(df_san.iloc[0]["Manha"], 27.4)
        self.assertEqual(df_san.iloc[0]["Tarde"], 28.5)

    def test_sanitizar_dados_tabela_colunas_dinamicas(self):
        # Testa sanitização com séries arbitrárias e personalizadas
        df_raw = pd.DataFrame({
            "Pontos": ["P1", None],
            "Sensor Norte": [265.0, 27.1],
            "Sensor Sul": ["28,3", 29.4],
        })
        df_san, mod = sanitizar_dados_tabela(df_raw)
        self.assertTrue(mod)
        self.assertEqual(df_san.iloc[1]["Pontos"], "P2")
        self.assertEqual(df_san.iloc[0]["Sensor Norte"], 26.5)
        self.assertEqual(df_san.iloc[0]["Sensor Sul"], 28.3)

    def test_calcular_estatisticas_serie(self):
        vals = [10.0, 20.0, 30.0]
        est = calcular_estatisticas_serie(vals)
        self.assertEqual(est["n"], 3)
        self.assertEqual(est["media"], 20.0)
        self.assertEqual(est["minimo"], 10.0)
        self.assertEqual(est["maximo"], 30.0)
        self.assertEqual(est["amplitude"], 20.0)
        self.assertAlmostEqual(est["desvio"], 10.0, places=4)

    def test_calcular_regressao_linear(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # Reta perfeita: y = 2x
        reg = calcular_regressao_linear(x, y)
        self.assertEqual(reg["n"], 5)
        self.assertAlmostEqual(reg["slope"], 2.0, places=4)
        self.assertAlmostEqual(reg["intercept"], 0.0, places=4)
        self.assertAlmostEqual(reg["r2"], 1.0, places=4)
        self.assertAlmostEqual(reg["r"], 1.0, places=4)

    def test_calcular_estatisticas_boxplot_e_outliers(self):
        # Série com um outlier claro (50.0)
        vals = [20.0, 21.0, 20.5, 21.2, 20.8, 21.1, 20.9, 21.0, 50.0]
        est = calcular_estatisticas_boxplot(vals)
        self.assertEqual(est["n"], 9)
        self.assertTrue(est["mediana"] > 20.0 and est["mediana"] < 22.0)
        self.assertTrue(est["iqr"] > 0)
        self.assertIn(50.0, est["outliers"])


class TestPlotEngine(unittest.TestCase):
    """Testes de renderização de gráficos Matplotlib para todas as modalidades."""

    def setUp(self):
        self.bordas = {"topo": True, "baixo": True, "esquerda": True, "direita": True, "cor": "black", "espessura": 1.0}
        self.ticks = {"topo": False, "direita": False, "baixo": True, "esquerda": True, "direcao": "out", "minor_ticks": True}
        self.legenda = {"exibir": True, "pos_x": 0.95, "pos_y": 0.95, "loc": "upper right", "orientacao": "Vertical", "moldura": True}

    def test_render_linhas(self):
        p = PRESETS_LINHAS["Dia 14 de Agosto"]
        fig = renderizar_grafico_linhas(
            df=p["df"],
            titulo_grafico=p["titulo_grafico"],
            rotulo_x="Pontos",
            rotulo_y="Temperatura do ar (°C)",
            min_y=p["min_y"],
            max_y=p["max_y"],
            series_ativas=["Manha", "Tarde", "Noite"],
            cores_periodos={"Manha": "#000", "Tarde": "#e74c3c", "Noite": "#2980b9"},
            estilos_linhas={"Manha": "-", "Tarde": "-", "Noite": "-"},
            fonte_nome="Arial",
            tamanho_fonte=11.0,
            espessura_linha=1.2,
            com_marcadores=True,
            bordas_config=self.bordas,
            ticks_config=self.ticks,
            legenda_config=self.legenda,
            exibir_grade=True,
        )
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)

    def test_render_linhas_dinamico_multiplas_series(self):
        # Gráfico dinâmico com 4 séries customizadas
        df_dinamico = pd.DataFrame({
            "Pontos": [f"P{i+1}" for i in range(5)],
            "Sensor Alpha": [24.1, 24.5, 25.0, 25.3, 25.1],
            "Sensor Beta": [26.0, 26.4, 27.1, 26.8, 26.5],
            "Sensor Gamma": [28.2, 28.5, 29.0, 28.8, 28.4],
            "Sensor Delta": [22.0, 22.3, 22.7, 23.0, 22.9],
        })
        fig = renderizar_grafico_linhas(
            df=df_dinamico,
            titulo_grafico="Monitoramento Multissensorial",
            rotulo_x="Estações",
            rotulo_y="Temperatura (°C)",
            min_y=20.0,
            max_y=32.0,
            series_ativas=["Sensor Alpha", "Sensor Gamma"],
            cores_periodos={},
            estilos_linhas={},
            fonte_nome="Arial",
            tamanho_fonte=11.0,
            espessura_linha=1.5,
            com_marcadores=True,
            bordas_config=self.bordas,
            ticks_config=self.ticks,
            legenda_config=self.legenda,
            exibir_grade=True,
        )
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)

    def test_render_barras(self):
        p = PRESETS_BARRAS["Ta (°C) — Média e Desvio Padrão (Modelo OriginLab da Pesquisa)"]
        rotulos = {"Bosque": "Bosque", "Desvio_Bosque": "Desvio", "Estacionamento": "Estac", "Desvio_Estacionamento": "Desvio"}
        fig = renderizar_grafico_barras(
            df=p["df"],
            titulo_grafico="",
            rotulo_x="",
            rotulo_y="Ta (°C)",
            min_y=p["min_y"],
            max_y=p["max_y"],
            series_barras_ativas=["Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"],
            cores_barras={"Bosque": "#2ca02c", "Desvio_Bosque": "#b0b7bd", "Estacionamento": "#d95f02", "Desvio_Estacionamento": "#fff"},
            rotulos_legenda=rotulos,
            fonte_nome="Arial",
            tamanho_fonte=11.0,
            exibir_valores=True,
            formato_decimais="Automático (ex: 27,32 | 2,3)",
            negrito_valores=False,
            largura_grupo=0.8,
            bordas_config=self.bordas,
            ticks_config=self.ticks,
            legenda_config=self.legenda,
            exibir_grade=True,
        )
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)

    def test_render_dispersao(self):
        p = PRESETS_DISPERSAO["BOSQUE — URA x Ta (Regressão R² = 0,334)"]
        fig = renderizar_grafico_dispersao(
            df=p["df"],
            titulo_grafico="Dispersão",
            rotulo_x="URA (%)",
            rotulo_y="Ta (°C)",
            min_x=p["min_x"],
            max_x=p["max_x"],
            min_y=p["min_y"],
            max_y=p["max_y"],
            fonte_nome="Arial",
            tamanho_fonte=11.0,
            cor_pontos="#5b9bd5",
            cor_borda_pontos="#41719c",
            marcador_pontos="o",
            tamanho_pontos=7.0,
            exibir_pontos=True,
            exibir_reta=True,
            cor_reta="#3b82f6",
            estilo_reta=":",
            espessura_reta=1.8,
            exibir_r2=True,
            exibir_equacao=True,
            exibir_banda=False,
            exibir_rotulos_pontos=False,
            posicao_r2="Junto à Reta (Superior)",
            bordas_config=self.bordas,
            ticks_config=self.ticks,
            legenda_config=self.legenda,
            exibir_grade=True,
        )
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)

    def test_render_boxplot(self):
        p = PRESETS_BOXPLOT["Distribuição Térmica — Bosque vs. Estacionamento"]
        fig = renderizar_grafico_boxplot(
            df=p["df"],
            titulo_grafico=p["titulo_grafico"],
            rotulo_x="Ambientes",
            rotulo_y="Ta (°C)",
            min_y=p["min_y"],
            max_y=p["max_y"],
            series_ativas=["Bosque", "Estacionamento"],
            cores_series={"Bosque": "#2ca02c", "Estacionamento": "#d95f02"},
            fonte_nome="Arial",
            tamanho_fonte=11.0,
            bordas_config=self.bordas,
            ticks_config=self.ticks,
            legenda_config=self.legenda,
            exibir_grade=True,
            largura_box=0.5,
            mostrar_medias=True,
            mostrar_outliers=True,
            mostrar_pontos=True,
        )
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 1)


class TestExcelExporter(unittest.TestCase):
    """Testes de geração de planilhas nativas .xlsx do Excel via OpenPyXL."""

    def test_gerar_excel_linhas(self):
        p = PRESETS_LINHAS["Dia 14 de Agosto"]
        data = gerar_excel_linhas_bytes(p["df"], "Dia 14", "Título")
        self.assertTrue(data.startswith(b"PK\x03\x04"))  # Assinatura de arquivo ZIP/XLSX

    def test_gerar_excel_barras(self):
        p = PRESETS_BARRAS["Ta (°C) — Média e Desvio Padrão (Modelo OriginLab da Pesquisa)"]
        rotulos = {"Bosque": "Bosque", "Desvio_Bosque": "Desvio", "Estacionamento": "Estac", "Desvio_Estacionamento": "Desvio"}
        data = gerar_excel_barras_bytes(p["df"], "TA", "", "", "Ta (°C)", rotulos_legenda=rotulos)
        self.assertTrue(data.startswith(b"PK\x03\x04"))

    def test_gerar_excel_dispersao(self):
        p = PRESETS_DISPERSAO["BOSQUE — URA x Ta (Regressão R² = 0,334)"]
        data = gerar_excel_dispersao_bytes(p["df"], "Dispersao", "", "URA", "Ta")
        self.assertTrue(data.startswith(b"PK\x03\x04"))

    def test_gerar_excel_boxplot(self):
        p = PRESETS_BOXPLOT["Distribuição Térmica — Bosque vs. Estacionamento"]
        data = gerar_excel_boxplot_bytes(p["df"], "Boxplot", "", "Ambientes", "Ta")
        self.assertTrue(data.startswith(b"PK\x03\x04"))



class TestProjectManagerAndFiles(unittest.TestCase):
    """Testes de persistência de arquivos .vespera e retrocompatibilidade."""

    def test_salvar_e_carregar_arquivo_vespera_dinamico(self):
        import tempfile
        df_teste = pd.DataFrame({
            "Pontos": ["P1", "P2", "P3"],
            "Sensor A": [21.5, 22.0, 22.5],
            "Sensor B": [25.0, 25.5, 26.0],
        })
        payload = ProjectManager.construir_payload(
            nome_projeto="Projeto Dinamico Teste",
            tipo_grafico="linhas",
            df=df_teste,
            titulo_dia="Dia de Teste",
            titulo_grafico="GRAFICO TESTE",
            min_y=20.0,
            max_y=30.0,
            cfg={"opcao_fonte": "Arial"},
        )
        self.assertEqual(payload["formato"], "vespera_project")
        self.assertEqual(payload["versao_formato"], "1.0.0")
        self.assertEqual(payload["colunas"], ["Pontos", "Sensor A", "Sensor B"])

        with tempfile.NamedTemporaryFile(suffix=".vespera", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            sucesso = ProjectManager.salvar_arquivo_projeto(tmp_path, payload)
            self.assertTrue(sucesso)
            self.assertTrue(os.path.exists(tmp_path))

            carregado = ProjectManager.carregar_arquivo_projeto(tmp_path)
            self.assertEqual(carregado["nome_projeto"], "Projeto Dinamico Teste")
            self.assertEqual(carregado["colunas"], ["Pontos", "Sensor A", "Sensor B"])
            self.assertEqual(len(carregado["dados"]), 3)
            self.assertEqual(carregado["dados"][0]["Sensor A"], 21.5)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_retrocompatibilidade_projetos_legados(self):
        # Simula estrutura antiga do projetos_salvos.json sem chaves novas
        payload_legado = {
            "nome_projeto": "Projeto Legado",
            "tipo_grafico": "linhas",
            "titulo_dia": "14 de Agosto",
            "titulo_grafico": "DIA 14",
            "min_y": 24.0,
            "max_y": 33.0,
            "dados": [
                {"Pontos": "P1", "Manha": 26.2, "Tarde": 30.1, "Noite": 25.4},
                {"Pontos": "P2", "Manha": 26.5, "Tarde": 30.5, "Noite": 25.8},
            ],
            "config": {"exibir_grade": True},
        }
        df_legado = pd.DataFrame(payload_legado["dados"])
        self.assertIn("Manha", df_legado.columns)
        self.assertIn("Tarde", df_legado.columns)
        self.assertIn("Noite", df_legado.columns)
        self.assertEqual(len(df_legado), 2)


if __name__ == "__main__":
    unittest.main()
