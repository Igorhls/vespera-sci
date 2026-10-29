"""
Suíte de Testes Automatizados Unitários e de Integração — Vespera Sci Desktop.
Cobre Sanitização, Estatísticas (Regressão e Boxplot), Motores de Plotagem e Exportação Excel.
"""

import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Assegura que o diretório raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanitizer import (  # noqa: E402
    calcular_banda_regressao,
    calcular_estatisticas_boxplot,
    calcular_estatisticas_serie,
    calcular_regressao_linear,
    detectar_escala_suspeita,
    formatar_numero_ptbr,
    quantil_t_975,
    sanitizar_dados_barras,
    sanitizar_dados_dispersao,
    sanitizar_dados_tabela,
)
from core.plot_engine import (  # noqa: E402
    MODO_DESVIO_BARRAS,
    MODO_DESVIO_ERRO,
    renderizar_grafico_barras,
    renderizar_grafico_boxplot,
    renderizar_grafico_dispersao,
    renderizar_grafico_linhas,
)
from core import paths, updater  # noqa: E402
from core.project_manager import ProjectManager  # noqa: E402
from core.updater import comparar_versoes, selecionar_asset_release, verificar_atualizacao_github  # noqa: E402
from core.excel_exporter import (  # noqa: E402
    gerar_excel_barras_bytes,
    gerar_excel_boxplot_bytes,
    gerar_excel_dispersao_bytes,
    gerar_excel_linhas_bytes,
)
from config.presets import PRESETS_BARRAS, PRESETS_BOXPLOT, PRESETS_DISPERSAO, PRESETS_LINHAS  # noqa: E402


class TestSanitizerAndStats(unittest.TestCase):
    """Testes de funções de sanitização de dados e cálculos estatísticos científicos."""

    def test_sanitizar_dados_tabela_escala(self):
        # Correção de valor que perdeu a vírgula (ex: 274.0 -> 27.4), somente quando solicitada
        df_raw = pd.DataFrame({
            "Pontos": [None, "P2"],
            "Manha": [274.0, 26.5],
            "Tarde": ["28,5", 29.0],
            "Noite": [25.0, 26.0],
        })
        df_san, mod = sanitizar_dados_tabela(df_raw, corrigir_escala=True)
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
        df_san, mod = sanitizar_dados_tabela(df_raw, corrigir_escala=True)
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

    def test_salvar_e_carregar_arquivo_json_padrao(self):
        import tempfile
        df_teste = pd.DataFrame({
            "Pontos": ["P1", "P2"],
            "Sensor X": [10.5, 11.2],
        })
        payload = ProjectManager.construir_payload(
            nome_projeto="Projeto JSON Padrao",
            tipo_grafico="linhas",
            df=df_teste,
            titulo_dia="Dia 1",
            titulo_grafico="",
            min_y=0.0,
            max_y=20.0,
            cfg={},
        )
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            sucesso = ProjectManager.salvar_arquivo_projeto(tmp_path, payload)
            self.assertTrue(sucesso)
            carregado = ProjectManager.carregar_arquivo_projeto(tmp_path)
            self.assertEqual(carregado["nome_projeto"], "Projeto JSON Padrao")
            self.assertEqual(carregado["colunas"], ["Pontos", "Sensor X"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

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



class TestUpdaterChannels(unittest.TestCase):
    """Testes do sistema de atualização com suporte a Canais Estável e Dev."""

    def test_comparar_versoes_semanticas(self):
        self.assertEqual(comparar_versoes("1.0.1", "1.0.0"), 1)
        self.assertEqual(comparar_versoes("v1.0.0", "1.0.0"), 0)
        self.assertEqual(comparar_versoes("1.0.0", "1.0.0"), 0)
        self.assertEqual(comparar_versoes("1.0.0", "1.2.0"), -1)
        self.assertEqual(comparar_versoes("2.0.0", "1.9.9"), 1)

    def test_comparar_versoes_pre_lancamento_dev(self):
        self.assertEqual(comparar_versoes("1.1.0-dev.1", "1.0.0"), 1)
        self.assertEqual(comparar_versoes("1.1.0-dev.2", "1.1.0-dev.1"), 1)
        self.assertEqual(comparar_versoes("1.1.0-dev.10", "1.1.0-dev.9"), 1)
        # Promover a versão para o estável é uma atualização para quem está no Dev
        self.assertEqual(comparar_versoes("1.1.0", "1.1.0-dev.3"), 1)
        self.assertEqual(comparar_versoes("v1.1.0-dev.1", "1.1.0-dev.1"), 0)

    def test_canal_dev_sem_sha_local_oferece_sincronizacao(self):
        respostas = [
            self._resposta(200, {"version": "1.0.0"}),
            self._resposta(200, {"sha": "b" * 40, "commit": {"message": "fix", "committer": {"date": "2026-10-28"}}}),
        ]
        with mock.patch("core.updater.ler_versao_local", return_value={"version": "1.0.0", "local_sha": ""}), \
                mock.patch("core.updater.requests.get", side_effect=respostas):
            res = verificar_atualizacao_github(canal="dev")
        self.assertTrue(res["tem_atualizacao"])

    @staticmethod
    def _resposta(status, payload):
        r = mock.Mock()
        r.status_code = status
        r.json.return_value = payload
        return r

    def test_verificar_canal_stable_estrutura(self):
        release = {
            "tag_name": "v99.0.0",
            "name": "Vespera Sci v99.0.0",
            "body": "Notas",
            "published_at": "2026-10-01T00:00:00Z",
            "html_url": "https://github.com/x/y/releases/tag/v99.0.0",
            "zipball_url": "https://api.github.com/zipball/v99.0.0",
            "assets": [],
        }
        with mock.patch("core.updater.requests.get", return_value=self._resposta(200, release)):
            res = verificar_atualizacao_github(canal="stable", timeout=8)
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["canal"], "stable")
        self.assertTrue(res["tem_atualizacao"])
        self.assertEqual(res["versao_remota"], "99.0.0")
        self.assertEqual(res["download_url"], release["zipball_url"])

    def test_verificar_canal_stable_sem_release(self):
        with mock.patch("core.updater.requests.get", return_value=self._resposta(404, {})):
            res = verificar_atualizacao_github(canal="stable")
        self.assertTrue(res["sucesso"])
        self.assertFalse(res["tem_atualizacao"])

    def test_verificar_canal_dev_estrutura(self):
        respostas = [
            self._resposta(200, {"version": "1.0.0", "notes": ""}),
            self._resposta(200, {"sha": "a" * 40, "commit": {"message": "feat: x", "committer": {"date": "2026-10-01"}}}),
        ]
        with mock.patch("core.updater.requests.get", side_effect=respostas):
            res = verificar_atualizacao_github(canal="dev", timeout=8)
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["canal"], "dev")
        self.assertIn("tem_atualizacao", res)
        self.assertEqual(res["sha_remoto"], "aaaaaaa")

    def test_canal_dev_indisponivel_no_executavel(self):
        with mock.patch("core.updater.executando_empacotado", return_value=True):
            res = verificar_atualizacao_github(canal="dev")
        self.assertFalse(res["sucesso"])

    def test_versao_local_lida_dos_recursos(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "version.json"), "w", encoding="utf-8") as f:
                json.dump({"version": "7.8.9"}, f)
            with mock.patch("core.updater.diretorio_recursos", return_value=tmp), \
                    mock.patch("core.updater.executando_empacotado", return_value=True):
                self.assertEqual(updater.ler_versao_local()["version"], "7.8.9")

    def test_selecionar_asset_por_plataforma(self):
        assets = [
            {"name": "VesperaSci-Windows-x64.zip"},
            {"name": "VesperaSci-macOS-AppleSilicon-arm64.dmg"},
            {"name": "VesperaSci-macOS-Intel-x86_64.dmg"},
        ]
        self.assertEqual(selecionar_asset_release(assets, "win32")["name"], "VesperaSci-Windows-x64.zip")
        self.assertEqual(selecionar_asset_release(assets, "darwin", "arm64")["name"], "VesperaSci-macOS-AppleSilicon-arm64.dmg")
        self.assertEqual(selecionar_asset_release(assets, "darwin", "x86_64")["name"], "VesperaSci-macOS-Intel-x86_64.dmg")
        self.assertIsNone(selecionar_asset_release(assets, "linux"))

    def test_download_com_sha256_divergente_e_rejeitado(self):
        resp = mock.Mock()
        resp.headers = {"content-length": "3"}
        resp.iter_content.return_value = [b"abc"]
        resp.raise_for_status.return_value = None
        with mock.patch("core.updater.requests.get", return_value=resp):
            with self.assertRaises(ValueError):
                updater._baixar("https://x", io.BytesIO(), lambda *a: None, sha256_esperado="0" * 64)

    def test_git_pull_com_falha_nao_sobrescreve_repositorio(self):
        falha = mock.Mock(returncode=1, stdout="", stderr="error: local changes would be overwritten")
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".git"))
            with mock.patch("core.updater.diretorio_codigo_fonte", return_value=tmp), \
                    mock.patch("core.updater.executando_empacotado", return_value=False), \
                    mock.patch("core.updater.subprocess.run", return_value=falha), \
                    mock.patch("core.updater.requests.get") as get:
                res = updater.baixar_e_aplicar_atualizacao(canal="dev")
        self.assertFalse(res["sucesso"])
        get.assert_not_called()

    def test_pacote_codigo_fonte_remove_modulos_obsoletos(self):
        with tempfile.TemporaryDirectory() as raiz, tempfile.TemporaryDirectory() as origem:
            for base, arquivos in ((raiz, ["core/antigo.py", "core/mantido.py", "main.py"]),
                                   (origem, ["core/mantido.py", "core/novo.py", "main.py"])):
                for rel in arquivos:
                    caminho = os.path.join(base, rel)
                    os.makedirs(os.path.dirname(caminho), exist_ok=True)
                    open(caminho, "w").close()
            removidos = updater._aplicar_pacote_codigo_fonte(origem, raiz)
            self.assertEqual(removidos, [os.path.join("core", "antigo.py")])
            self.assertTrue(os.path.exists(os.path.join(raiz, "core", "novo.py")))
            self.assertTrue(os.path.exists(os.path.join(raiz, "core", "mantido.py")))

    def test_staging_windows_gera_script_sem_tocar_na_instalacao(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("VesperaSci/VesperaSci.exe", b"novo")
        conteudo = buf.getvalue()

        resp = mock.Mock()
        resp.headers = {"content-length": str(len(conteudo))}
        resp.iter_content.return_value = [conteudo]
        resp.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as instalacao:
            exe_atual = os.path.join(instalacao, "VesperaSci.exe")
            with open(exe_atual, "wb") as f:
                f.write(b"antigo")
            with mock.patch("core.updater.sys.platform", "win32"), \
                    mock.patch("core.updater.diretorio_instalacao", return_value=instalacao), \
                    mock.patch("core.updater.requests.get", return_value=resp):
                res = updater._atualizar_empacotado("https://x/VesperaSci-Windows-x64.zip", "", lambda *a: None)
            self.assertTrue(res["sucesso"])
            self.assertEqual(res["acao_pos"], updater.ACAO_APLICAR_AO_FECHAR)
            with open(exe_atual, "rb") as f:
                self.assertEqual(f.read(), b"antigo")
            with open(res["script"], encoding="utf-8") as f:
                self.assertIn("robocopy", f.read())
            os.remove(res["script"])


class TestCorrecoesRegressao(unittest.TestCase):
    """Regressões dos bugs corrigidos na revisão de outubro/2026."""

    def setUp(self):
        self.bordas = {"topo": False, "baixo": True, "esquerda": True, "direita": False, "cor": "black", "espessura": 1.0}
        self.ticks = {"topo": False, "direita": False, "baixo": True, "esquerda": True, "direcao": "out", "minor_ticks": True}
        self.legenda = {"exibir": True, "pos_x": 0.95, "pos_y": 0.95, "loc": "upper right", "orientacao": "Vertical", "moldura": True}

    def tearDown(self):
        plt.close("all")

    # --- Sanitizador -------------------------------------------------------
    def test_sanitizador_nao_altera_valores_legitimos(self):
        df = pd.DataFrame({"Pontos": ["P1", "P2"], "Pressao": [1013.2, 1009.8], "Umid": [75.0, 82.0], "CO2": ["415", "420,5"]})
        df_san, _ = sanitizar_dados_tabela(df)
        self.assertEqual(df_san["Pressao"].tolist(), [1013.2, 1009.8])
        self.assertEqual(df_san["Umid"].tolist(), [75.0, 82.0])
        self.assertEqual(df_san["CO2"].tolist(), [415.0, 420.5])

    def test_sanitizador_barras_nao_altera_valores_legitimos(self):
        df = pd.DataFrame({"Mes": ["Jan"], "Bosque": [250.0], "Desvio_Bosque": [12.0],
                           "Estacionamento": [300.0], "Desvio_Estacionamento": [9.0]})
        df_san, _ = sanitizar_dados_barras(df)
        self.assertEqual(df_san.iloc[0]["Bosque"], 250.0)

    def test_sanitizar_dispersao_converte_virgula(self):
        df = pd.DataFrame({"Ponto": [None], "X": ["1,5"], "Y": ["2,25"]})
        df_san, _ = sanitizar_dados_dispersao(df)
        self.assertEqual(df_san.iloc[0]["Ponto"], "P1")
        self.assertEqual(df_san.iloc[0]["X"], 1.5)
        self.assertEqual(df_san.iloc[0]["Y"], 2.25)

    def test_detectar_escala_suspeita(self):
        self.assertTrue(detectar_escala_suspeita(["274", "265", "28"]))
        # Qualquer separador decimal no bloco indica que a vírgula não se perdeu
        self.assertFalse(detectar_escala_suspeita(["274", "26,5"]))
        self.assertFalse(detectar_escala_suspeita(["25", "30", "abc"]))

    def test_formatar_numero_ptbr(self):
        self.assertEqual(formatar_numero_ptbr(27.30), "27,3")
        self.assertEqual(formatar_numero_ptbr(2.3, "2 Casas Decimais Fixas"), "2,30")

    # --- Estatística ---------------------------------------------------------
    def test_quantil_t(self):
        self.assertAlmostEqual(quantil_t_975(1), 12.7062, places=4)
        self.assertAlmostEqual(quantil_t_975(10), 2.2281, places=4)
        self.assertAlmostEqual(quantil_t_975(60), 2.0003, places=3)
        self.assertAlmostEqual(quantil_t_975(120), 1.9799, places=3)

    def test_banda_confianca_regressao(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        y = np.array([2.1, 3.9, 6.2, 7.8, 10.1, 12.2])
        reg = calcular_regressao_linear(x, y)
        inf, sup = calcular_banda_regressao(reg, x)
        # Referência: fórmula clássica do IC da média ajustada com t(0,975; n-2)
        n = len(x)
        y_hat = reg["slope"] * x + reg["intercept"]
        meia = 2.7764 * reg["se"] * np.sqrt(1 / n + (x - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
        np.testing.assert_allclose(sup - y_hat, meia, rtol=1e-4)
        np.testing.assert_allclose(y_hat - inf, meia, rtol=1e-4)
        # A banda é mais estreita no centro dos dados
        larguras = sup - inf
        self.assertLess(larguras[2], larguras[0])
        # Predição é sempre mais larga que confiança
        inf_p, sup_p = calcular_banda_regressao(reg, x, predicao=True)
        self.assertTrue(np.all(sup_p - inf_p > larguras))

    def test_banda_indisponivel_com_dois_pontos(self):
        reg = calcular_regressao_linear([1.0, 2.0], [1.0, 3.0])
        self.assertIsNone(calcular_banda_regressao(reg, [1.0, 2.0]))

    # --- Motor de gráficos ---------------------------------------------------
    def _linhas(self, df, **kw):
        args = dict(
            df=df, titulo_grafico="", rotulo_x="", rotulo_y="", min_y=None, max_y=None,
            series_ativas=None, cores_periodos={}, estilos_linhas={}, fonte_nome="Arial",
            tamanho_fonte=10.0, espessura_linha=1.0, com_marcadores=True,
            bordas_config=self.bordas, ticks_config=self.ticks, legenda_config=self.legenda, exibir_grade=True,
        )
        args.update(kw)
        return renderizar_grafico_linhas(**args)

    def test_linhas_sem_dados_nao_quebra(self):
        df = pd.DataFrame({"Pontos": ["P1", "P2"], "A": [np.nan, np.nan]})
        self._linhas(df)
        self._linhas(df, min_y=0.0, max_y=35.0, series_ativas=["A"])
        self._linhas(pd.DataFrame({"Pontos": []}))

    def test_linhas_marcadores_vazados(self):
        df = pd.DataFrame({"Pontos": ["P1", "P2"], "Manha": [20.0, 21.0]})
        fig = self._linhas(df, marcadores_vazados=True)
        self.assertEqual(fig.axes[0].lines[0].get_markerfacecolor(), "white")

    def test_bordas_respeitadas_em_todos_os_graficos(self):
        figs = [
            self._linhas(pd.DataFrame({"Pontos": ["P1"], "A": [1.0]})),
            renderizar_grafico_dispersao(
                df=pd.DataFrame({"Ponto": ["P1", "P2", "P3"], "X": [1.0, 2.0, 3.0], "Y": [2.0, 4.1, 5.9]}),
                titulo_grafico="", rotulo_x="", rotulo_y="", min_x=None, max_x=None, min_y=None, max_y=None,
                fonte_nome="Arial", tamanho_fonte=10.0, cor_pontos="#000", cor_borda_pontos="#000",
                marcador_pontos="o", tamanho_pontos=5.0, exibir_pontos=True, exibir_reta=True, cor_reta="#00f",
                estilo_reta="-", espessura_reta=1.0, exibir_r2=True, exibir_equacao=True, exibir_banda=True,
                exibir_rotulos_pontos=False, posicao_r2="Superior Esquerdo", bordas_config=self.bordas,
                ticks_config=self.ticks, legenda_config=self.legenda, exibir_grade=False,
            ),
            renderizar_grafico_boxplot(
                df=pd.DataFrame({"Ponto": ["P1", "P2", "P3"], "A": [1.0, 2.0, 3.0]}),
                titulo_grafico="", rotulo_x="", rotulo_y="", min_y=None, max_y=None, series_ativas=[],
                cores_series={}, fonte_nome="Arial", tamanho_fonte=10.0, bordas_config=self.bordas,
                ticks_config=self.ticks, legenda_config=self.legenda, exibir_grade=False,
            ),
        ]
        for fig in figs:
            ax = fig.axes[0]
            self.assertFalse(ax.spines["top"].get_visible())
            self.assertFalse(ax.spines["right"].get_visible())
            self.assertTrue(ax.spines["bottom"].get_visible())
            self.assertTrue(ax.spines["left"].get_visible())

    def _barras(self, df, modo, ativas=None):
        return renderizar_grafico_barras(
            df=df, titulo_grafico="", rotulo_x="", rotulo_y="", min_y=0.0, max_y=40.0,
            series_barras_ativas=ativas or ["Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"],
            cores_barras={}, rotulos_legenda={}, fonte_nome="Arial", tamanho_fonte=10.0, exibir_valores=True,
            formato_decimais="Automático", negrito_valores=False, largura_grupo=0.7, bordas_config=self.bordas,
            ticks_config=self.ticks, legenda_config=self.legenda, exibir_grade=True, modo_desvio=modo,
        )

    def test_barras_modo_erro_desenha_barra_de_erro(self):
        df = pd.DataFrame({"Mes": ["Ago", "Dez"], "Bosque": [27.3, 28.6], "Desvio_Bosque": [2.3, 1.4],
                           "Estacionamento": [28.5, 29.4], "Desvio_Estacionamento": [4.9, 2.2]})
        ax = self._barras(df, MODO_DESVIO_ERRO).axes[0]
        self.assertEqual(len(ax.patches), 4)  # 2 meses x 2 médias
        from matplotlib.container import BarContainer
        barras = [c for c in ax.containers if isinstance(c, BarContainer)]
        self.assertEqual(len(barras), 2)
        self.assertTrue(all(c.errorbar is not None for c in barras))
        ax_legado = self._barras(df, MODO_DESVIO_BARRAS).axes[0]
        self.assertEqual(len(ax_legado.patches), 8)  # 2 meses x 4 séries

    def test_barras_ignora_celulas_vazias(self):
        df = pd.DataFrame({"Mes": ["Ago", "Dez"], "Bosque": [27.3, np.nan], "Desvio_Bosque": [2.3, np.nan],
                           "Estacionamento": [np.nan, np.nan], "Desvio_Estacionamento": [np.nan, np.nan]})
        ax = self._barras(df, MODO_DESVIO_BARRAS).axes[0]
        alturas = [p.get_height() for p in ax.patches]
        self.assertEqual(sorted(alturas), [2.3, 27.3])

    def _boxplot(self, df, ativas, controladas, pontos=False):
        return renderizar_grafico_boxplot(
            df=df, titulo_grafico="", rotulo_x="", rotulo_y="", min_y=None, max_y=None, series_ativas=ativas,
            cores_series={}, fonte_nome="Arial", tamanho_fonte=10.0, bordas_config=self.bordas,
            ticks_config=self.ticks, legenda_config=self.legenda, exibir_grade=False, mostrar_pontos=pontos,
            series_controladas=controladas,
        )

    def test_boxplot_series_controladas(self):
        df = pd.DataFrame({"Ponto": ["P1", "P2"], "Bosque": [1.0, 2.0], "Estacionamento": [3.0, 4.0], "Ambiente C": [5.0, 6.0]})
        ax = self._boxplot(df, ["Bosque"], ["Bosque", "Estacionamento"]).axes[0]
        self.assertEqual([t.get_text() for t in ax.get_xticklabels()], ["Bosque", "Ambiente C"])
        ax_vazio = self._boxplot(df[["Ponto", "Bosque"]], [], ["Bosque", "Estacionamento"]).axes[0]
        self.assertEqual(len(ax_vazio.patches), 0)

    def test_boxplot_jitter_reprodutivel(self):
        df = pd.DataFrame({"Ponto": [f"P{i}" for i in range(6)], "A": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})
        a = self._boxplot(df, [], None, pontos=True).axes[0].collections[0].get_offsets()
        b = self._boxplot(df, [], None, pontos=True).axes[0].collections[0].get_offsets()
        np.testing.assert_array_equal(np.asarray(a), np.asarray(b))

    # --- Persistência --------------------------------------------------------
    def test_banco_de_projetos_na_pasta_do_usuario(self):
        with tempfile.TemporaryDirectory() as dados, tempfile.TemporaryDirectory() as fonte:
            with open(os.path.join(fonte, "projetos_salvos.json"), "w", encoding="utf-8") as f:
                json.dump({"ultimo_projeto_ativo": None, "projetos": {"Legado": {"dados": []}}}, f)
            with mock.patch("core.project_manager.diretorio_dados_usuario", return_value=dados), \
                    mock.patch("core.project_manager.diretorio_codigo_fonte", return_value=fonte):
                pm = ProjectManager()
            self.assertEqual(os.path.dirname(pm.caminho_banco), dados)
            self.assertIn("Legado", pm.ler_banco()["projetos"])

    def test_gravacao_atomica_preserva_arquivo_em_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "projeto.json")
            paths.gravar_json_atomico(caminho, {"ok": 1})
            with self.assertRaises(TypeError):
                paths.gravar_json_atomico(caminho, {"invalido": object()})
            with open(caminho, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"ok": 1})
            self.assertEqual(os.listdir(tmp), ["projeto.json"])


if __name__ == "__main__":
    unittest.main()
