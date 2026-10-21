"""
Janela Principal (QMainWindow) do Vespera Sci Desktop.
Repaginação visual completa: ícones vetoriais SVG nítidos, logotipo oficial Vespera Alpha,
eliminação total de emojis e barras responsivas sem cortes horizontais.
"""

import json
import os
import numpy as np
import pandas as pd
from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from config.presets import PRESETS_BARRAS, PRESETS_BOXPLOT, PRESETS_DISPERSAO, PRESETS_LINHAS
from config.themes import DEFAULT_CONFIG
from core.excel_exporter import (
    gerar_excel_barras_bytes,
    gerar_excel_boxplot_bytes,
    gerar_excel_dispersao_bytes,
    gerar_excel_linhas_bytes,
)
from core.plot_engine import (
    renderizar_grafico_barras,
    renderizar_grafico_boxplot,
    renderizar_grafico_dispersao,
    renderizar_grafico_linhas,
)
from core.project_manager import ProjectManager
from ui.data_table_widget import DataTableWidget
from ui.icons import get_icon
from ui.plot_canvas_widget import PlotCanvasWidget
from ui.sidebar_controls import SidebarControlsWidget
from ui.styles import THEME_DARK, THEME_LIGHT, build_qss


class VesperaMainWindow(QMainWindow):
    """Janela principal do estúdio científico Vespera Sci."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vespera Sci v1.0.0 (Beta) — Estúdio Científico de Dados e Gráficos")
        self.resize(1760, 920)
        self.setMinimumSize(1280, 720)

        # Ícone oficial da janela e da barra de tarefas
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.project_manager = ProjectManager()
        self.banco_projetos = self.project_manager.ler_banco()

        self.tipo_grafico_atual = "linhas"
        self.nome_projeto_atual = "Dia 14 de agosto"
        self.cfg_atual = DEFAULT_CONFIG.copy()
        self._updating_project_combo = False
        self.settings = QSettings("VesperaSci", "VesperaSci")
        self.tema_atual = str(self.settings.value("theme", "light"))
        saved_geom = self.settings.value("geometry")
        if saved_geom:
            self.restoreGeometry(saved_geom)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(75)
        self._debounce_timer.timeout.connect(self._executar_atualizacao_grafico)

        self._apply_theme()
        self._build_menu()
        self._build_ui()
        self._inicializar_sessao()

    
    def closeEvent(self, event):
        try:
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("theme", self.tema_atual)
        except Exception:
            pass
        super().closeEvent(event)

    def _apply_theme(self):
        tema = THEME_DARK if self.tema_atual == "dark" else THEME_LIGHT
        self.setStyleSheet(build_qss(tema))

    def _alternar_tema(self):
        self.tema_atual = "dark" if self.tema_atual == "light" else "light"
        self._apply_theme()
        if self.tema_atual == "dark":
            self.btn_toggle_theme.setText("Modo Claro")
            self.btn_toggle_theme.setIcon(get_icon("sun", color="#fbbf24", size=16))
        else:
            self.btn_toggle_theme.setText("Modo Escuro")
            self.btn_toggle_theme.setIcon(get_icon("moon", color="#6366f1", size=16))

    def _alternar_submenu(self):
        if self.submenu_dialog.isVisible():
            self.submenu_dialog.hide()
            self.btn_toggle_submenu.setChecked(False)
        else:
            geom = self.geometry()
            self.submenu_dialog.move(geom.x() + 30, geom.y() + 80)
            self.submenu_dialog.show()
            self.submenu_dialog.raise_()
            self.submenu_dialog.activateWindow()
            self.btn_toggle_submenu.setChecked(True)

    def _alternar_tabela(self):
        visivel = self.table_widget.isVisible()
        if visivel and not self.plot_widget.isVisible():
            return
        self.table_widget.setVisible(not visivel)
        self.btn_toggle_table.setChecked(not visivel)

    def _alternar_grafico(self):
        visivel = self.plot_widget.isVisible()
        if visivel and not self.table_widget.isVisible():
            return
        self.plot_widget.setVisible(not visivel)
        self.btn_toggle_plot.setChecked(not visivel)

    def _build_menu(self):
        menubar = self.menuBar()

        menu_arq = menubar.addMenu("&Arquivo")

        act_salvar = QAction("Salvar Projeto Atual", self)
        act_salvar.setIcon(get_icon("save", size=16))
        act_salvar.setShortcut(QKeySequence.Save)
        act_salvar.triggered.connect(self._salvar_projeto_atual)
        menu_arq.addAction(act_salvar)

        act_imp_json = QAction("Importar Projeto (.json / .vespera)...", self)
        act_imp_json.setIcon(get_icon("folder", size=16))
        act_imp_json.triggered.connect(self._importar_arquivo_projeto)
        menu_arq.addAction(act_imp_json)

        act_imp_xlsx = QAction("Importar Planilha (.xlsx / .csv)...", self)
        act_imp_xlsx.setIcon(get_icon("file-spreadsheet", size=16))
        act_imp_xlsx.triggered.connect(self._importar_planilha)
        menu_arq.addAction(act_imp_xlsx)

        act_exp_svg = QAction("Exportar Gráfico em SVG Vetorial...", self)
        act_exp_svg.setIcon(get_icon("download", size=16))
        act_exp_svg.triggered.connect(lambda: self.plot_widget._exportar_svg() if hasattr(self, "plot_widget") else None)
        menu_arq.addAction(act_exp_svg)

        menu_arq.addSeparator()

        act_sair = QAction("Sair", self)
        act_sair.setShortcut(QKeySequence.Quit)
        act_sair.triggered.connect(self.close)
        menu_arq.addAction(act_sair)

        menu_exibir = menubar.addMenu("&Exibir")
        act_tema = QAction("Alternar Tema Claro / Escuro", self)
        act_tema.setIcon(get_icon("moon", size=16))
        act_tema.triggered.connect(self._alternar_tema)
        menu_exibir.addAction(act_tema)

        menu_exibir.addSeparator()

        act_sub = QAction("Submenu de Configurações do Gráfico...", self)
        act_sub.setIcon(get_icon("sliders", size=16))
        act_sub.setShortcut(QKeySequence("Ctrl+E"))
        act_sub.triggered.connect(self._alternar_submenu)
        menu_exibir.addAction(act_sub)

        act_table = QAction("Alternar Tabela de Dados", self)
        act_table.setIcon(get_icon("table", size=16))
        act_table.setShortcut(QKeySequence("Ctrl+T"))
        act_table.triggered.connect(self._alternar_tabela)
        menu_exibir.addAction(act_table)

        act_plot = QAction("Alternar Visualizador do Gráfico", self)
        act_plot.setIcon(get_icon("chart-line", size=16))
        act_plot.setShortcut(QKeySequence("Ctrl+G"))
        act_plot.triggered.connect(self._alternar_grafico)
        menu_exibir.addAction(act_plot)

        menu_ajuda = menubar.addMenu("A&juda")
        act_update = QAction("Verificar Atualizações no GitHub...", self)
        act_update.setIcon(get_icon("github", size=16))
        act_update.triggered.connect(self._acionar_verificacao_atualizacao)
        menu_ajuda.addAction(act_update)

        act_sobre = QAction("Sobre o Vespera Sci", self)
        act_sobre.setIcon(get_icon("app-icon", size=16))
        act_sobre.triggered.connect(self._mostrar_sobre)
        menu_ajuda.addAction(act_sobre)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(8)

        # -------------------------------------------------------------------
        # 1. Header Bar Unificado (Identidade Visual Alpha + Modos + Ações)
        # -------------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("headerBar")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(10)

        # Marca & Identidade Alpha
        brand_widget = QWidget()
        bw_layout = QHBoxLayout(brand_widget)
        bw_layout.setContentsMargins(0, 0, 0, 0)
        bw_layout.setSpacing(8)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "app_icon.png")
        if os.path.exists(icon_path):
            lbl_logo = QLabel()
            pix = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            bw_layout.addWidget(lbl_logo)

        lbl_brand = QLabel(
            "<b>Vespera Sci</b> <span style='background-color: #3b82f6; color: white; "
            "font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;'>BETA</span>"
        )
        lbl_brand.setStyleSheet("font-size: 15px;")
        bw_layout.addWidget(lbl_brand)
        header_layout.addWidget(brand_widget)

        header_layout.addStretch()

        # Segmented Switcher para Linhas vs Barras
        self.btn_modo_linhas = QPushButton("Linhas (Pontos P1–Pn)")
        self.btn_modo_linhas.setIcon(get_icon("chart-line", size=16))
        self.btn_modo_linhas.setObjectName("btnSegmentActive")
        self.btn_modo_linhas.setCursor(Qt.PointingHandCursor)
        self.btn_modo_linhas.clicked.connect(lambda: self._alternar_modo("linhas"))

        self.btn_modo_barras = QPushButton("Barras (Média & Desvio)")
        self.btn_modo_barras.setIcon(get_icon("chart-bar", size=16))
        self.btn_modo_barras.setObjectName("btnSegment")
        self.btn_modo_barras.setCursor(Qt.PointingHandCursor)
        self.btn_modo_barras.clicked.connect(lambda: self._alternar_modo("barras"))

        self.btn_modo_dispersao = QPushButton("Dispersão (Regressão R²)")
        self.btn_modo_dispersao.setIcon(get_icon("chart-scatter", size=16))
        self.btn_modo_dispersao.setObjectName("btnSegment")
        self.btn_modo_dispersao.setCursor(Qt.PointingHandCursor)
        self.btn_modo_dispersao.clicked.connect(lambda: self._alternar_modo("dispersao"))

        self.btn_modo_boxplot = QPushButton("Boxplot (Distribuição)")
        self.btn_modo_boxplot.setIcon(get_icon("sliders", size=16))
        self.btn_modo_boxplot.setObjectName("btnSegment")
        self.btn_modo_boxplot.setCursor(Qt.PointingHandCursor)
        self.btn_modo_boxplot.clicked.connect(lambda: self._alternar_modo("boxplot"))

        header_layout.addWidget(self.btn_modo_linhas)
        header_layout.addWidget(self.btn_modo_barras)
        header_layout.addWidget(self.btn_modo_dispersao)
        header_layout.addWidget(self.btn_modo_boxplot)

        header_layout.addStretch()

        # Controles de Exibição dos Painéis e Submenu
        self.btn_toggle_submenu = QPushButton("Configurações")
        self.btn_toggle_submenu.setIcon(get_icon("sliders", size=16))
        self.btn_toggle_submenu.setCheckable(True)
        self.btn_toggle_submenu.setChecked(False)
        self.btn_toggle_submenu.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_submenu.setToolTip("Abrir/Fechar Submenu de Configurações e Estilo do Gráfico (Ctrl+E)")
        self.btn_toggle_submenu.clicked.connect(self._alternar_submenu)

        self.btn_toggle_table = QPushButton("Tabela")
        self.btn_toggle_table.setIcon(get_icon("table", size=16))
        self.btn_toggle_table.setCheckable(True)
        self.btn_toggle_table.setChecked(True)
        self.btn_toggle_table.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_table.setToolTip("Exibir/Ocultar Tabela de Dados e Estatísticas (Ctrl+T)")
        self.btn_toggle_table.clicked.connect(self._alternar_tabela)

        self.btn_toggle_plot = QPushButton("Gráfico")
        self.btn_toggle_plot.setIcon(get_icon("chart-line", size=16))
        self.btn_toggle_plot.setCheckable(True)
        self.btn_toggle_plot.setChecked(True)
        self.btn_toggle_plot.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_plot.setToolTip("Exibir/Ocultar Visualizador do Gráfico (Ctrl+G)")
        self.btn_toggle_plot.clicked.connect(self._alternar_grafico)

        header_layout.addWidget(self.btn_toggle_submenu)
        header_layout.addWidget(self.btn_toggle_table)
        header_layout.addWidget(self.btn_toggle_plot)

        # Botão alternar tema Claro / Escuro
        self.btn_toggle_theme = QPushButton("Modo Escuro")
        self.btn_toggle_theme.setIcon(get_icon("moon", color="#6366f1", size=16))
        self.btn_toggle_theme.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_theme.clicked.connect(self._alternar_tema)
        header_layout.addWidget(self.btn_toggle_theme)

        # Botão auto-update
        self.btn_check_update = QPushButton("GitHub")
        self.btn_check_update.setIcon(get_icon("github", size=16))
        self.btn_check_update.setCursor(Qt.PointingHandCursor)
        self.btn_check_update.clicked.connect(self._acionar_verificacao_atualizacao)
        header_layout.addWidget(self.btn_check_update)

        root_layout.addWidget(header_frame)

        # -------------------------------------------------------------------
        # 2. Barra Superior de Gerenciamento de Projetos (Responsiva)
        # -------------------------------------------------------------------
        proj_frame = QFrame()
        proj_frame.setObjectName("projBar")
        proj_layout = QHBoxLayout(proj_frame)
        proj_layout.setContentsMargins(10, 6, 10, 6)
        proj_layout.setSpacing(8)

        proj_layout.addWidget(QLabel("<b>Projeto:</b>"))
        self.txt_nome_projeto = QLineEdit()
        self.txt_nome_projeto.setPlaceholderText("Nome do projeto...")
        self.txt_nome_projeto.setMinimumWidth(160)
        proj_layout.addWidget(self.txt_nome_projeto)

        self.btn_salvar_proj = QPushButton("Salvar (Ctrl+S)")
        self.btn_salvar_proj.setIcon(get_icon("save", color="#ffffff", size=16))
        self.btn_salvar_proj.setObjectName("btnPrimary")
        self.btn_salvar_proj.setCursor(Qt.PointingHandCursor)
        self.btn_salvar_proj.clicked.connect(self._salvar_projeto_atual)
        proj_layout.addWidget(self.btn_salvar_proj)

        proj_layout.addWidget(QLabel("<b>Salvos:</b>"))
        self.cmb_projetos_salvos = QComboBox()
        self.cmb_projetos_salvos.setMinimumWidth(180)
        self.cmb_projetos_salvos.currentIndexChanged.connect(self._on_projeto_salvo_selecionado)
        proj_layout.addWidget(self.cmb_projetos_salvos, stretch=1)

        self.btn_exportar_json = QPushButton("Backup (.json)")
        self.btn_exportar_json.setIcon(get_icon("download", size=16))
        self.btn_exportar_json.setCursor(Qt.PointingHandCursor)
        self.btn_exportar_json.clicked.connect(self._exportar_projeto_json)
        proj_layout.addWidget(self.btn_exportar_json)

        self.btn_excluir_proj = QPushButton("Excluir")
        self.btn_excluir_proj.setIcon(get_icon("trash", color="#dc2626", size=16))
        self.btn_excluir_proj.setObjectName("btnDanger")
        self.btn_excluir_proj.setCursor(Qt.PointingHandCursor)
        self.btn_excluir_proj.clicked.connect(self._excluir_projeto_atual)
        proj_layout.addWidget(self.btn_excluir_proj)

        root_layout.addWidget(proj_frame)

        # -------------------------------------------------------------------
        # 3. Área Principal Dividida: Tabela de Dados e Gráfico Científico
        # -------------------------------------------------------------------
        self.splitter = QSplitter(Qt.Horizontal)

        self.table_widget = DataTableWidget()
        self.plot_widget = PlotCanvasWidget()

        self.splitter.addWidget(self.table_widget)
        self.splitter.addWidget(self.plot_widget)
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, True)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([750, 950])

        # Habilitar divisores interativos com auto-ajuste responsivo à tela
        for i in range(self.splitter.count()):
            h = self.splitter.handle(i)
            if h:
                h.setEnabled(True)

        root_layout.addWidget(self.splitter, stretch=1)

        # -------------------------------------------------------------------
        # 4. Submenu Flutuante Não-Modal de Configurações e Estilo do Gráfico
        # -------------------------------------------------------------------
        self.sidebar = SidebarControlsWidget()

        self.submenu_dialog = QDialog(self, Qt.Tool | Qt.WindowCloseButtonHint)
        self.submenu_dialog.setWindowTitle("Configurações & Estilo do Gráfico — Vespera Sci")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "app_icon.png")
        if os.path.exists(icon_path):
            self.submenu_dialog.setWindowIcon(QIcon(icon_path))

        sub_layout = QVBoxLayout(self.submenu_dialog)
        sub_layout.setContentsMargins(4, 4, 4, 4)
        sub_layout.addWidget(self.sidebar)
        self.submenu_dialog.resize(360, 760)
        self.submenu_dialog.finished.connect(lambda r=0: self.btn_toggle_submenu.setChecked(False))

        # Barra de status inferior
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Conexão de sinais
        self.sidebar.configChanged.connect(self._on_sidebar_config_changed)
        self.sidebar.modeChangeRequested.connect(self._alternar_modo)
        self.sidebar.presetSelected.connect(self._carregar_preset)
        self.sidebar.importSpreadsheetRequested.connect(self._importar_planilha)
        self.sidebar.importProjectFileRequested.connect(self._importar_arquivo_projeto)
        self.sidebar.hideRequested.connect(self._alternar_submenu)

        self.table_widget.dataOrMetaChanged.connect(self._on_table_meta_changed)
        self.table_widget.hideRequested.connect(self._alternar_tabela)

        self.plot_widget.seriesVisibilityChanged.connect(self.atualizar_grafico)
        self.plot_widget.exportExcelRequested.connect(self._exportar_planilha_excel)
        self.plot_widget.hideRequested.connect(self._alternar_grafico)
        self.plot_widget.configRequested.connect(self._alternar_submenu)

    def _inicializar_sessao(self):
        self._atualizar_combo_projetos()
        ultimo = self.banco_projetos.get("ultimo_projeto_ativo")
        projetos_dict = self.banco_projetos.get("projetos", {})
        if ultimo and ultimo in projetos_dict:
            self._aplicar_projeto_dict(projetos_dict[ultimo])
            self.status_bar.showMessage(f"Projeto '{ultimo}' restaurado.")
        else:
            self._carregar_preset("Dia 14 de Agosto")
            self.status_bar.showMessage("Pronto. Selecione um modelo ou edite os valores na matriz de dados.")

    def _atualizar_botoes_modo(self):
        self.btn_modo_linhas.setObjectName("btnSegmentActive" if self.tipo_grafico_atual == "linhas" else "btnSegment")
        self.btn_modo_barras.setObjectName("btnSegmentActive" if self.tipo_grafico_atual == "barras" else "btnSegment")
        self.btn_modo_dispersao.setObjectName("btnSegmentActive" if self.tipo_grafico_atual == "dispersao" else "btnSegment")
        for btn in (self.btn_modo_linhas, self.btn_modo_barras, self.btn_modo_dispersao):
            self.style().unpolish(btn)
            self.style().polish(btn)

    def _alternar_modo(self, novo_modo: str):
        if novo_modo == self.tipo_grafico_atual:
            return
        if novo_modo == "barras":
            self._carregar_preset("Ta (°C) — Média e Desvio Padrão (Modelo OriginLab da Pesquisa)")
        elif novo_modo == "dispersao":
            self._carregar_preset("BOSQUE — URA x Ta (Regressão R² = 0,334)")
        elif novo_modo == "boxplot":
            self._carregar_preset("Distribuição Térmica — Bosque vs. Estacionamento")
        else:
            self._carregar_preset("Dia 14 de Agosto")

    def _carregar_preset(self, nome_preset: str):
        cfg = self.sidebar.obter_config()
        cfg.update(self.plot_widget.obter_estado_series())

        if nome_preset in PRESETS_BARRAS:
            p = PRESETS_BARRAS[nome_preset]
            self.tipo_grafico_atual = "barras"
            self.nome_projeto_atual = p.get("nome_projeto", "TA - Média e Desvio Padrão")
            cfg["rotulo_x"] = p["rotulo_x"]
            cfg["rotulo_y"] = p["rotulo_y"]
            cfg["rotulo_s1"] = p.get("rotulo_s1", "Bosque")
            cfg["rotulo_s2"] = p.get("rotulo_s2", "Desvio/p (Bosque)")
            cfg["rotulo_s3"] = p.get("rotulo_s3", "Estacionamento")
            cfg["rotulo_s4"] = p.get("rotulo_s4", "Desvio/p (Estacionamento)")
            cfg["opcao_fonte"] = "Arial (Científico Internacional)"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = False
            cfg["ticks_dir"] = False
            if "config" in p:
                cfg.update(p["config"])
            df_alvo = p["df"].copy()
            titulo_dia = p["titulo_dia"]
            titulo_grafico = p["titulo_grafico"]
            min_y, max_y = p["min_y"], p["max_y"]

        elif nome_preset in PRESETS_LINHAS:
            p = PRESETS_LINHAS[nome_preset]
            self.tipo_grafico_atual = "linhas"
            self.nome_projeto_atual = p["titulo_dia"]
            cfg["rotulo_x"] = "Pontos"
            cfg["rotulo_y"] = "Temperatura do ar (°C)"
            cfg["direcao_ticks"] = "Para dentro (in)"
            cfg["ticks_topo"] = True
            cfg["ticks_dir"] = True
            df_alvo = p["df"].copy()
            titulo_dia = p["titulo_dia"]
            titulo_grafico = p["titulo_grafico"]
            min_y, max_y = p["min_y"], p["max_y"]

        elif nome_preset in PRESETS_DISPERSAO:
            p = PRESETS_DISPERSAO[nome_preset]
            self.tipo_grafico_atual = "dispersao"
            self.nome_projeto_atual = p.get("nome_projeto", "Dispersão URA x Ta")
            cfg["rotulo_x"] = p["rotulo_x"]
            cfg["rotulo_y"] = p["rotulo_y"]
            cfg["rotulo_s1"] = p.get("rotulo_s1", "Pontos Experimentais")
            cfg["rotulo_s2"] = p.get("rotulo_s2", "Reta de Ajuste Linear")
            cfg["opcao_fonte"] = "Arial (Científico Internacional)"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = True
            cfg["ticks_dir"] = True
            if "config" in p:
                cfg.update(p["config"])
            df_alvo = p["df"].copy()
            titulo_dia = p["titulo_dia"]
            titulo_grafico = p["titulo_grafico"]
            min_y, max_y = p["min_y"], p["max_y"]

        elif nome_preset == "Criar Novo — Dispersão (X vs Y)":
            self.tipo_grafico_atual = "dispersao"
            self.nome_projeto_atual = "Novo Projeto - Dispersão"
            cfg["rotulo_x"] = "Variável X"
            cfg["rotulo_y"] = "Variável Y"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = True
            cfg["ticks_dir"] = True
            df_alvo = pd.DataFrame({
                "Ponto": [f"P{i}" for i in range(1, 11)],
                "X": [10.0 + i for i in range(10)],
                "Y": [20.0 + i * 1.5 for i in range(10)],
            })
            titulo_dia = "X vs Y"
            titulo_grafico = "DISPERSÃO X vs Y"
            min_y, max_y = 15.0, 40.0

        elif nome_preset in PRESETS_BOXPLOT:
            p = PRESETS_BOXPLOT[nome_preset]
            self.tipo_grafico_atual = "boxplot"
            self.nome_projeto_atual = p.get("titulo_dia", "Distribuição Térmica")
            cfg["rotulo_x"] = p["rotulo_x"]
            cfg["rotulo_y"] = p["rotulo_y"]
            cfg["opcao_fonte"] = "Arial (Científico Internacional)"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = True
            cfg["ticks_dir"] = True
            df_alvo = p["df"].copy()
            titulo_dia = p["titulo_dia"]
            titulo_grafico = p["titulo_grafico"]
            min_y, max_y = p["min_y"], p["max_y"]

        elif nome_preset == "Criar Novo — Boxplot (Distribuição)":
            self.tipo_grafico_atual = "boxplot"
            self.nome_projeto_atual = "Novo Projeto - Boxplot"
            cfg["rotulo_x"] = "Ambientes Amostrais"
            cfg["rotulo_y"] = "Ta (°C)"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = True
            cfg["ticks_dir"] = True
            df_alvo = pd.DataFrame({
                "Ponto": [f"P{i}" for i in range(1, 11)],
                "Bosque": [26.0 + (i*0.2) for i in range(10)],
                "Estacionamento": [28.0 + (i*0.35) for i in range(10)],
            })
            titulo_dia = "Distribuição Térmica"
            titulo_grafico = "COMPARAÇÃO DE DISTRIBUIÇÃO"
            min_y, max_y = 20.0, 36.0

        elif nome_preset == "Criar Novo — Barras (Média e Desvio)":
            self.tipo_grafico_atual = "barras"
            self.nome_projeto_atual = "Novo Projeto - Média e Desvio"
            cfg["rotulo_x"] = "TA"
            cfg["rotulo_y"] = "Média (%)"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = False
            cfg["ticks_dir"] = False
            df_alvo = pd.DataFrame({
                "Mes": ["Agosto", "Dezembro"],
                "Bosque": [25.0, 26.0],
                "Desvio_Bosque": [2.0, 1.5],
                "Estacionamento": [28.0, 29.0],
                "Desvio_Estacionamento": [3.0, 2.0],
            })
            titulo_dia = "TA"
            titulo_grafico = ""
            min_y, max_y = 0.0, 35.0

        else:
            self.tipo_grafico_atual = "linhas"
            self.nome_projeto_atual = "Novo Projeto"
            cfg["rotulo_x"] = "Pontos"
            cfg["rotulo_y"] = "Temperatura do ar (°C)"
            cfg["direcao_ticks"] = "Para dentro (in)"
            cfg["ticks_topo"] = True
            cfg["ticks_dir"] = True
            df_alvo = pd.DataFrame({
                "Pontos": [f"P{i}" for i in range(1, 11)],
                "Manha": [25.0] * 10,
                "Tarde": [30.0] * 10,
                "Noite": [26.0] * 10,
            })
            titulo_dia = "Novo Dia"
            titulo_grafico = "NOVO DIA - BOSQUE"
            min_y, max_y = 20.0, 35.0

        self.txt_nome_projeto.setText(self.nome_projeto_atual)
        self.sidebar.carregar_config(cfg, self.tipo_grafico_atual)
        self.plot_widget.carregar_estado_series(cfg)
        self.table_widget.carregar_dados_e_meta(
            self.tipo_grafico_atual, df_alvo, titulo_dia, titulo_grafico, min_y, max_y, cfg
        )
        self._atualizar_botoes_modo()
        self.atualizar_grafico()

    def _aplicar_projeto_dict(self, proj_dict: dict):
        tipo = proj_dict.get("tipo_grafico", "linhas")
        self.tipo_grafico_atual = tipo
        self.nome_projeto_atual = proj_dict.get("nome_projeto", proj_dict.get("titulo_dia", "Meu Projeto"))
        self.txt_nome_projeto.setText(self.nome_projeto_atual)

        default_tit = "BOSQUE URA x Ta" if tipo == "dispersao" else ("TA" if tipo == "barras" else "Dia 14 de agosto")
        default_graf = "BOSQUE URA x Ta" if tipo == "dispersao" else ("" if tipo == "barras" else "DIA 14 DE AGOSTO - BOSQUE")
        default_min_y = 34.5 if tipo == "dispersao" else (0.0 if tipo == "barras" else 24.0)
        default_max_y = 38.0 if tipo == "dispersao" else (35.0 if tipo == "barras" else 33.0)

        titulo_dia = proj_dict.get("titulo_dia", default_tit)
        titulo_grafico = proj_dict.get("titulo_grafico", default_graf)
        min_y = float(proj_dict.get("min_y", default_min_y))
        max_y = float(proj_dict.get("max_y", default_max_y))

        registros = proj_dict.get("dados", [])
        if tipo == "dispersao":
            if registros:
                df_loaded = pd.DataFrame(registros)
                cols_d = ["Ponto", "X", "Y"]
                for col in cols_d:
                    if col not in df_loaded.columns:
                        df_loaded[col] = np.nan if col != "Ponto" else ""
                df_alvo = df_loaded[cols_d].copy()
            else:
                df_alvo = PRESETS_DISPERSAO["BOSQUE — URA x Ta (Regressão R² = 0,334)"]["df"].copy()
        elif tipo == "barras":
            if registros:
                df_loaded = pd.DataFrame(registros)
                cols_b = ["Mes", "Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
                for col in cols_b:
                    if col not in df_loaded.columns:
                        df_loaded[col] = np.nan if col != "Mes" else ""
                df_alvo = df_loaded[cols_b].copy()
            else:
                df_alvo = PRESETS_BARRAS["TA — Média e Desvio Padrão (Agosto e Dezembro)"]["df"].copy()
        else:
            if registros:
                df_loaded = pd.DataFrame(registros)
                cols_l = ["Pontos", "Manha", "Tarde", "Noite"]
                for col in cols_l:
                    if col not in df_loaded.columns:
                        df_loaded[col] = np.nan if col != "Pontos" else ""
                df_alvo = df_loaded[cols_l].copy()
            else:
                df_alvo = PRESETS_LINHAS["Dia 14 de Agosto"]["df"].copy()

        cfg = DEFAULT_CONFIG.copy()
        cfg.update(proj_dict.get("config", {}))

        self.sidebar.carregar_config(cfg, tipo)
        self.plot_widget.carregar_estado_series(cfg)
        self.table_widget.carregar_dados_e_meta(tipo, df_alvo, titulo_dia, titulo_grafico, min_y, max_y, cfg)
        self._atualizar_botoes_modo()
        self.atualizar_grafico()

    def _on_sidebar_config_changed(self):
        side_passo = self.sidebar.spn_intervalo_ticks_y.value()
        if abs(self.table_widget.spn_intervalo_ticks_y.value() - side_passo) > 1e-4:
            self.table_widget.spn_intervalo_ticks_y.blockSignals(True)
            self.table_widget.spn_intervalo_ticks_y.setValue(side_passo)
            self.table_widget.spn_intervalo_ticks_y.blockSignals(False)

        side_passo_x = self.sidebar.spn_intervalo_ticks_x.value()
        if abs(self.table_widget.spn_intervalo_ticks_x.value() - side_passo_x) > 1e-4:
            self.table_widget.spn_intervalo_ticks_x.blockSignals(True)
            self.table_widget.spn_intervalo_ticks_x.setValue(side_passo_x)
            self.table_widget.spn_intervalo_ticks_x.blockSignals(False)

        if self.sidebar.txt_rotulo_x.text() != self.table_widget.txt_rotulo_x.text():
            self.table_widget.txt_rotulo_x.blockSignals(True)
            self.table_widget.txt_rotulo_x.setText(self.sidebar.txt_rotulo_x.text())
            self.table_widget.txt_rotulo_x.blockSignals(False)

        if self.sidebar.txt_rotulo_y.text() != self.table_widget.txt_rotulo_y.text():
            self.table_widget.txt_rotulo_y.blockSignals(True)
            self.table_widget.txt_rotulo_y.setText(self.sidebar.txt_rotulo_y.text())
            self.table_widget.txt_rotulo_y.blockSignals(False)

        side_sub = self.sidebar.spn_espaco_subgrupos.value()
        if abs(self.table_widget.spn_espaco_subgrupos.value() - side_sub) > 1e-4:
            self.table_widget.spn_espaco_subgrupos.blockSignals(True)
            self.table_widget.spn_espaco_subgrupos.setValue(side_sub)
            self.table_widget.spn_espaco_subgrupos.blockSignals(False)

        self.atualizar_grafico()

    def _on_table_meta_changed(self):
        meta_passo = self.table_widget.spn_intervalo_ticks_y.value()
        if abs(self.sidebar.spn_intervalo_ticks_y.value() - meta_passo) > 1e-4:
            self.sidebar.spn_intervalo_ticks_y.blockSignals(True)
            self.sidebar.spn_intervalo_ticks_y.setValue(meta_passo)
            self.sidebar.spn_intervalo_ticks_y.blockSignals(False)

        meta_passo_x = self.table_widget.spn_intervalo_ticks_x.value()
        if abs(self.sidebar.spn_intervalo_ticks_x.value() - meta_passo_x) > 1e-4:
            self.sidebar.spn_intervalo_ticks_x.blockSignals(True)
            self.sidebar.spn_intervalo_ticks_x.setValue(meta_passo_x)
            self.sidebar.spn_intervalo_ticks_x.blockSignals(False)

        if self.table_widget.txt_rotulo_x.text() != self.sidebar.txt_rotulo_x.text():
            self.sidebar.txt_rotulo_x.blockSignals(True)
            self.sidebar.txt_rotulo_x.setText(self.table_widget.txt_rotulo_x.text())
            self.sidebar.txt_rotulo_x.blockSignals(False)

        if self.table_widget.txt_rotulo_y.text() != self.sidebar.txt_rotulo_y.text():
            self.sidebar.txt_rotulo_y.blockSignals(True)
            self.sidebar.txt_rotulo_y.setText(self.table_widget.txt_rotulo_y.text())
            self.sidebar.txt_rotulo_y.blockSignals(False)

        meta_sub = self.table_widget.spn_espaco_subgrupos.value()
        if abs(self.sidebar.spn_espaco_subgrupos.value() - meta_sub) > 1e-4:
            self.sidebar.spn_espaco_subgrupos.blockSignals(True)
            self.sidebar.spn_espaco_subgrupos.setValue(meta_sub)
            self.sidebar.spn_espaco_subgrupos.blockSignals(False)

        self.atualizar_grafico()

    def atualizar_grafico(self):
        if hasattr(self, "_debounce_timer"):
            self._debounce_timer.start(75)
        else:
            self._executar_atualizacao_grafico()

    def _executar_atualizacao_grafico(self):
        df = self.table_widget.obter_dataframe_atual()
        meta = self.table_widget.obter_metadados()
        cfg = self.sidebar.obter_config()

        rotulos_barras = {
            "Bosque": meta["rotulo_s1"],
            "Desvio_Bosque": meta["rotulo_s2"],
            "Estacionamento": meta["rotulo_s3"],
            "Desvio_Estacionamento": meta["rotulo_s4"],
        }

        self.plot_widget.configurar_modo(self.tipo_grafico_atual, rotulos_barras)
        self.plot_widget.definir_nome_base_exportacao(meta["titulo_dia"] or self.txt_nome_projeto.text())

        bordas_config = {
            "topo": cfg["borda_top"],
            "baixo": cfg["borda_bottom"],
            "esquerda": cfg["borda_left"],
            "direita": cfg["borda_right"],
            "cor": cfg["cor_moldura"],
            "espessura": cfg["esp_moldura"],
        }
        ticks_config = {
            "topo": cfg["ticks_topo"],
            "direita": cfg["ticks_dir"],
            "baixo": cfg["ticks_baixo"],
            "esquerda": cfg["ticks_esq"],
            "direcao": "in" if "dentro" in cfg["direcao_ticks"] else "out",
            "minor_ticks": cfg["minor_ticks"],
            "intervalo_y": float(cfg.get("intervalo_ticks_y", 0.0)),
            "intervalo_x": float(cfg.get("intervalo_ticks_x", 0.0)),
        }
        legenda_config = {
            "exibir": cfg["exibir_legenda"],
            "pos_x": cfg["leg_x"],
            "pos_y": cfg["leg_y"],
            "loc": self.sidebar.obter_loc_ancora_legenda(),
            "orientacao": cfg["orientacao_leg"].split(" ")[0],
            "moldura": cfg["moldura_legenda"],
        }

        if self.tipo_grafico_atual == "linhas":
            modo_linhas = cfg.get("modo_estilo_linhas", "Opção 1: Linha + Símbolo (Line + Symbol)")
            descritivo = cfg.get("rotulos_descritivos_legenda", True)
            tamanho_marcador = float(cfg.get("tamanho_marcador", 6.0))

            if "Opção 1" in modo_linhas or (cfg.get("com_marcadores") and not cfg.get("com_linhas_distintas")):
                estilos_linhas = {"Manha": "-", "Tarde": "-", "Noite": "-"}
                com_marcadores = True
                marcadores_map = {"Manha": "o", "Tarde": "s", "Noite": "^"}
                rotulos_legenda = (
                    {"Manha": "Manhã (Bolinha)", "Tarde": "Tarde (Quadrado)", "Noite": "Noite (Triângulo)"}
                    if descritivo
                    else {"Manha": "Manhã", "Tarde": "Tarde", "Noite": "Noite"}
                )
            elif "Opção 2" in modo_linhas or (cfg.get("com_linhas_distintas") and not cfg.get("com_marcadores")):
                estilos_linhas = {"Manha": "--", "Tarde": "-", "Noite": ":"}
                com_marcadores = False
                marcadores_map = None
                rotulos_legenda = (
                    {"Manha": "Manhã (Tracejada)", "Tarde": "Tarde (Contínua)", "Noite": "Noite (Pontilhada)"}
                    if descritivo
                    else {"Manha": "Manhã", "Tarde": "Tarde", "Noite": "Noite"}
                )
            elif "Personalizado" in modo_linhas:
                estilos_linhas = {
                    "Manha": cfg.get("traco_manha", "-"),
                    "Tarde": cfg.get("traco_tarde", "-"),
                    "Noite": cfg.get("traco_noite", "-"),
                }
                marcadores_map = {
                    "Manha": cfg.get("marcador_manha", "o"),
                    "Tarde": cfg.get("marcador_tarde", "s"),
                    "Noite": cfg.get("marcador_noite", "^"),
                }
                com_marcadores = any(v not in (None, "", "None") for v in marcadores_map.values())
                rotulos_legenda = {"Manha": "Manhã", "Tarde": "Tarde", "Noite": "Noite"}
            else:
                estilos_linhas = {"Manha": "-", "Tarde": "-", "Noite": "-"}
                com_marcadores = False
                marcadores_map = None
                rotulos_legenda = {"Manha": "Manhã", "Tarde": "Tarde", "Noite": "Noite"}

            renderizar_grafico_linhas(
                df=df,
                titulo_grafico=meta["titulo_grafico"],
                rotulo_x=meta["rotulo_x"],
                rotulo_y=meta["rotulo_y"],
                min_y=meta["min_y"],
                max_y=meta["max_y"],
                series_ativas=self.plot_widget.obter_series_linhas_ativas(),
                cores_periodos=self.sidebar.obter_cores_linhas_ativas(),
                estilos_linhas=estilos_linhas,
                fonte_nome=cfg["opcao_fonte"],
                tamanho_fonte=cfg["tamanho_fonte"],
                espessura_linha=cfg["espessura_linha"],
                com_marcadores=com_marcadores,
                bordas_config=bordas_config,
                ticks_config=ticks_config,
                legenda_config=legenda_config,
                exibir_grade=cfg["exibir_grade"],
                fig=self.plot_widget.fig,
                marcadores_map=marcadores_map,
                rotulos_legenda=rotulos_legenda,
                tamanho_marcador=tamanho_marcador,
            )
        elif self.tipo_grafico_atual == "dispersao":
            cores_disp = self.sidebar.obter_cores_dispersao_ativas()
            series_ativas = self.plot_widget.obter_series_dispersao_ativas()
            renderizar_grafico_dispersao(
                df=df,
                titulo_grafico=meta["titulo_grafico"],
                rotulo_x=meta["rotulo_x"],
                rotulo_y=meta["rotulo_y"],
                min_x=meta.get("min_x", 0.0),
                max_x=meta.get("max_x", 0.0),
                min_y=meta["min_y"],
                max_y=meta["max_y"],
                fonte_nome=cfg["opcao_fonte"],
                tamanho_fonte=cfg["tamanho_fonte"],
                cor_pontos=cores_disp.get("pontos", "#5b9bd5"),
                cor_borda_pontos=cores_disp.get("borda_pontos", "#41719c"),
                marcador_pontos=cfg.get("marcador_pontos_dispersao", "o"),
                tamanho_pontos=float(cfg.get("tamanho_pontos_dispersao", 7.0)),
                exibir_pontos=series_ativas.get("pontos", True),
                exibir_reta=series_ativas.get("reta", True) and cfg.get("exibir_reta_dispersao", True),
                cor_reta=cores_disp.get("reta", "#3b82f6"),
                estilo_reta=cfg.get("estilo_reta_dispersao", ":"),
                espessura_reta=float(cfg.get("espessura_reta_dispersao", 1.8)),
                exibir_r2=series_ativas.get("r2", True) and cfg.get("exibir_r2_dispersao", True),
                exibir_equacao=cfg.get("exibir_equacao_dispersao", False),
                exibir_banda=cfg.get("exibir_banda_dispersao", False),
                exibir_rotulos_pontos=cfg.get("exibir_rotulos_pontos_dispersao", False),
                posicao_r2=cfg.get("posicao_r2_dispersao", "Junto à Reta (Superior)"),
                bordas_config=bordas_config,
                ticks_config=ticks_config,
                legenda_config=legenda_config,
                exibir_grade=cfg["exibir_grade"],
                fig=self.plot_widget.fig,
                intervalo_ticks_x=float(cfg.get("intervalo_ticks_x", 0.0)),
                intervalo_ticks_y=float(cfg.get("intervalo_ticks_y", 0.0)),
            )
        elif self.tipo_grafico_atual == "boxplot":
            renderizar_grafico_boxplot(
                df=df,
                titulo_grafico=meta["titulo_grafico"],
                rotulo_x=meta["rotulo_x"],
                rotulo_y=meta["rotulo_y"],
                min_y=meta["min_y"],
                max_y=meta["max_y"],
                series_ativas=self.plot_widget.obter_series_boxplot_ativas(),
                cores_series={"Bosque": "#2ca02c", "Estacionamento": "#d95f02", "Ambiente A": "#3b82f6", "Ambiente B": "#f59e0b"},
                fonte_nome=cfg["opcao_fonte"],
                tamanho_fonte=cfg["tamanho_fonte"],
                bordas_config=bordas_config,
                ticks_config=ticks_config,
                legenda_config=legenda_config,
                exibir_grade=cfg["exibir_grade"],
                largura_box=cfg.get("largura_box", 0.5),
                mostrar_medias=cfg.get("mostrar_medias", True),
                mostrar_outliers=cfg.get("mostrar_outliers", True),
                mostrar_pontos=cfg.get("mostrar_pontos_jitter", False),
                intervalo_ticks_y=float(cfg.get("intervalo_ticks_y", 0.0)),
                fig=self.plot_widget.fig,
            )
        else:
            renderizar_grafico_barras(
                df=df,
                titulo_grafico=meta["titulo_grafico"],
                rotulo_x=meta["rotulo_x"],
                rotulo_y=meta["rotulo_y"],
                min_y=meta["min_y"],
                max_y=meta["max_y"],
                series_barras_ativas=self.plot_widget.obter_series_barras_ativas(),
                cores_barras=self.sidebar.obter_cores_barras_ativas(),
                rotulos_legenda=rotulos_barras,
                fonte_nome=cfg["opcao_fonte"],
                tamanho_fonte=cfg["tamanho_fonte"],
                exibir_valores=cfg["exibir_valores_barras"],
                formato_decimais=cfg["formato_decimais_barras"],
                negrito_valores=cfg["negrito_valores_barras"],
                largura_grupo=cfg["largura_grupo_barras"],
                bordas_config=bordas_config,
                ticks_config=ticks_config,
                legenda_config=legenda_config,
                exibir_grade=cfg["exibir_grade"],
                fig=self.plot_widget.fig,
                hachuras_barras=self.sidebar.obter_hachuras_barras_ativas(),
                espaco_subgrupos=float(cfg.get("espaco_subgrupos_barras", 0.35)),
                espaco_barras=float(cfg.get("espaco_barras", 0.0)),
            )

        self.plot_widget.atualizar_canvas()

    def _construir_payload_atual(self) -> dict:
        meta = self.table_widget.obter_metadados()
        cfg = self.sidebar.obter_config()
        cfg.update(self.plot_widget.obter_estado_series())
        cfg.update({
            "rotulo_x": meta["rotulo_x"],
            "rotulo_y": meta["rotulo_y"],
            "rotulo_s1": meta["rotulo_s1"],
            "rotulo_s2": meta["rotulo_s2"],
            "rotulo_s3": meta["rotulo_s3"],
            "rotulo_s4": meta["rotulo_s4"],
        })
        nome = (self.txt_nome_projeto.text().strip() or meta["titulo_dia"].strip() or "Meu Projeto")
        return self.project_manager.construir_payload(
            nome_projeto=nome,
            tipo_grafico=self.tipo_grafico_atual,
            df=self.table_widget.obter_dataframe_atual(),
            titulo_dia=meta["titulo_dia"],
            titulo_grafico=meta["titulo_grafico"],
            min_y=meta["min_y"],
            max_y=meta["max_y"],
            cfg=cfg,
        )

    def _atualizar_combo_projetos(self):
        self._updating_project_combo = True
        self.cmb_projetos_salvos.clear()
        projetos = self.banco_projetos.get("projetos", {})
        self.cmb_projetos_salvos.addItem(f"Projetos salvos ({len(projetos)})...", None)
        for nome, p in projetos.items():
            tipo_p = p.get("tipo_grafico")
            tipo_str = "Dispersão" if tipo_p == "dispersao" else ("Barras" if tipo_p == "barras" else "Linhas")
            data_str = p.get("atualizado_em", "")
            self.cmb_projetos_salvos.addItem(f"{nome} [{tipo_str}] ({data_str})", nome)
        self._updating_project_combo = False

    def _salvar_projeto_atual(self):
        payload = self._construir_payload_atual()
        nome_final = payload["nome_projeto"]
        self.banco_projetos.setdefault("projetos", {})[nome_final] = payload
        self.banco_projetos["ultimo_projeto_ativo"] = nome_final
        self.project_manager.gravar_banco(self.banco_projetos)
        self.nome_projeto_atual = nome_final
        self.txt_nome_projeto.setText(nome_final)
        self._atualizar_combo_projetos()
        self.status_bar.showMessage(f"Projeto '{nome_final}' salvo com sucesso em {payload['atualizado_em']}.")

    def _on_projeto_salvo_selecionado(self, index: int):
        if self._updating_project_combo or index <= 0:
            return
        nome = self.cmb_projetos_salvos.itemData(index)
        projetos = self.banco_projetos.get("projetos", {})
        if nome and nome in projetos:
            self._aplicar_projeto_dict(projetos[nome])
            self.banco_projetos["ultimo_projeto_ativo"] = nome
            self.project_manager.gravar_banco(self.banco_projetos)
            self.status_bar.showMessage(f"Projeto '{nome}' carregado com sucesso.")
        self._updating_project_combo = True
        self.cmb_projetos_salvos.setCurrentIndex(0)
        self._updating_project_combo = False

    def _excluir_projeto_atual(self):
        alvo = self.txt_nome_projeto.text().strip() or self.nome_projeto_atual
        projetos = self.banco_projetos.get("projetos", {})
        if alvo not in projetos:
            QMessageBox.information(self, "Excluir Projeto", f"O projeto '{alvo}' não está na lista de salvos.")
            return
        resp = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja remover o projeto '{alvo}' da lista de projetos salvos?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            del projetos[alvo]
            if self.banco_projetos.get("ultimo_projeto_ativo") == alvo:
                restantes = list(projetos.keys())
                self.banco_projetos["ultimo_projeto_ativo"] = restantes[-1] if restantes else None
            self.project_manager.gravar_banco(self.banco_projetos)
            self._atualizar_combo_projetos()
            self.status_bar.showMessage(f"Projeto '{alvo}' excluído.")

    def _exportar_projeto_json(self):
        payload = self._construir_payload_atual()
        nome_arq = f"{payload['nome_projeto'].replace(' ', '_').lower()}_vespera.json"
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Arquivo de Projeto (.json)",
            nome_arq,
            "Projeto Vespera Sci (*.json *.vespera)",
        )
        if caminho:
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                self.status_bar.showMessage(f"Backup do projeto salvo em: {caminho}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Exportar Projeto", str(e))

    def _importar_arquivo_projeto(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Arquivo de Projeto (.json / .vespera)",
            "",
            "Projeto Vespera Sci (*.json *.vespera)",
        )
        if caminho:
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    proj = json.load(f)
                if isinstance(proj, dict) and "dados" in proj:
                    self._aplicar_projeto_dict(proj)
                    nome_imp = self.nome_projeto_atual
                    self.banco_projetos.setdefault("projetos", {})[nome_imp] = proj
                    self.banco_projetos["ultimo_projeto_ativo"] = nome_imp
                    self.project_manager.gravar_banco(self.banco_projetos)
                    self._atualizar_combo_projetos()
                    self.status_bar.showMessage(f"Projeto '{nome_imp}' importado e salvo!")
                else:
                    QMessageBox.warning(self, "Formato Inválido", "O arquivo selecionado não é um projeto válido.")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Importar Projeto", str(e))

    def _importar_planilha(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Planilha (.xlsx ou .csv)",
            "",
            "Planilhas (*.xlsx *.csv)",
        )
        if not caminho:
            return
        try:
            df_up = pd.read_csv(caminho) if caminho.lower().endswith(".csv") else pd.read_excel(caminho)
            col_map = {}
            for c in df_up.columns:
                c_clean = str(c).strip().lower()
                if "ponto" in c_clean:
                    col_map[c] = "Pontos"
                elif "manh" in c_clean or "manha" in c_clean:
                    col_map[c] = "Manha"
                elif "tarde" in c_clean:
                    col_map[c] = "Tarde"
                elif "noite" in c_clean:
                    col_map[c] = "Noite"

            df_mapped = df_up.rename(columns=col_map)
            cols_req = ["Pontos", "Manha", "Tarde", "Noite"]
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
            cfg = self.sidebar.obter_config()

            if all(c in df_mapped.columns for c in cols_req):
                self.tipo_grafico_atual = "linhas"
                self.nome_projeto_atual = nome_base
                self.txt_nome_projeto.setText(nome_base)
                self.table_widget.carregar_dados_e_meta(
                    "linhas",
                    df_mapped[cols_req].copy(),
                    nome_base,
                    f"{nome_base.upper()} - BOSQUE",
                    24.0,
                    33.0,
                    cfg,
                )
                self._atualizar_botoes_modo()
                self.atualizar_grafico()
                self.status_bar.showMessage(f"Planilha '{os.path.basename(caminho)}' importada com sucesso (Linhas).")
            elif len(df_up.columns) in (2, 3):
                # Importar como dispersão X vs Y
                if len(df_up.columns) == 2:
                    df_disp = pd.DataFrame({
                        "Ponto": [f"P{i+1}" for i in range(len(df_up))],
                        "X": pd.to_numeric(df_up.iloc[:, 0].astype(str).str.replace(",", "."), errors="coerce"),
                        "Y": pd.to_numeric(df_up.iloc[:, 1].astype(str).str.replace(",", "."), errors="coerce"),
                    })
                    col_x_name = str(df_up.columns[0])
                    col_y_name = str(df_up.columns[1])
                else:
                    df_disp = pd.DataFrame({
                        "Ponto": df_up.iloc[:, 0].astype(str),
                        "X": pd.to_numeric(df_up.iloc[:, 1].astype(str).str.replace(",", "."), errors="coerce"),
                        "Y": pd.to_numeric(df_up.iloc[:, 2].astype(str).str.replace(",", "."), errors="coerce"),
                    })
                    col_x_name = str(df_up.columns[1])
                    col_y_name = str(df_up.columns[2])

                self.tipo_grafico_atual = "dispersao"
                self.nome_projeto_atual = nome_base
                self.txt_nome_projeto.setText(nome_base)
                cfg["rotulo_x"] = col_x_name
                cfg["rotulo_y"] = col_y_name
                min_x = float(np.nanfloor(df_disp["X"].min())) if not df_disp["X"].isna().all() else 0.0
                max_x = float(np.nanceil(df_disp["X"].max())) if not df_disp["X"].isna().all() else 10.0
                min_y = float(np.nanfloor(df_disp["Y"].min())) if not df_disp["Y"].isna().all() else 0.0
                max_y = float(np.nanceil(df_disp["Y"].max())) if not df_disp["Y"].isna().all() else 10.0
                self.sidebar.carregar_config(cfg, "dispersao")
                self.table_widget.carregar_dados_e_meta(
                    "dispersao",
                    df_disp,
                    nome_base,
                    f"{col_x_name} x {col_y_name}",
                    min_y,
                    max_y,
                    cfg,
                    min_x=min_x,
                    max_x=max_x,
                )
                self._atualizar_botoes_modo()
                self.atualizar_grafico()
                self.status_bar.showMessage(f"Planilha '{os.path.basename(caminho)}' importada com sucesso (Dispersão X vs Y).")
            else:
                QMessageBox.warning(
                    self,
                    "Colunas Não Reconhecidas",
                    "A planilha deve conter 4 colunas para Linhas (Pontos, Manha, Tarde, Noite) "
                    "ou 2 a 3 colunas para Dispersão (Ponto, X, Y).",
                )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Ler Planilha", str(e))

    def _exportar_planilha_excel(self, caminho: str):
        try:
            df = self.table_widget.obter_dataframe_atual()
            meta = self.table_widget.obter_metadados()
            if self.tipo_grafico_atual == "linhas":
                excel_bytes = gerar_excel_linhas_bytes(
                    df=df,
                    titulo_dia=meta["titulo_dia"],
                    titulo_grafico=meta["titulo_grafico"],
                    min_y=meta["min_y"],
                    max_y=meta["max_y"],
                )
            elif self.tipo_grafico_atual == "dispersao":
                excel_bytes = gerar_excel_dispersao_bytes(
                    df=df,
                    titulo_tabela=meta["titulo_dia"],
                    titulo_grafico=meta["titulo_grafico"],
                    rotulo_x=meta["rotulo_x"],
                    rotulo_y=meta["rotulo_y"],
                    min_x=meta.get("min_x", 0.0),
                    max_x=meta.get("max_x", 0.0),
                    min_y=meta["min_y"],
                    max_y=meta["max_y"],
                )
            else:
                rotulos_legenda = {
                    "Bosque": meta["rotulo_s1"],
                    "Desvio_Bosque": meta["rotulo_s2"],
                    "Estacionamento": meta["rotulo_s3"],
                    "Desvio_Estacionamento": meta["rotulo_s4"],
                }
                excel_bytes = gerar_excel_barras_bytes(
                    df=df,
                    titulo_tabela=meta["titulo_dia"],
                    titulo_grafico=meta["titulo_grafico"],
                    rotulo_x=meta["rotulo_x"],
                    rotulo_y=meta["rotulo_y"],
                    min_y=meta["min_y"],
                    max_y=meta["max_y"],
                    rotulos_legenda=rotulos_legenda,
                )
            with open(caminho, "wb") as f:
                f.write(excel_bytes)
            QMessageBox.information(
                self, "Planilha Exportada", f"Planilha Excel com gráfico nativo salva em:\n{caminho}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar Planilha Excel", str(e))

    def _acionar_verificacao_atualizacao(self):
        try:
            from ui.update_dialog import UpdateDialog
            dlg = UpdateDialog(self)
            dlg.exec()
        except ImportError:
            QMessageBox.information(
                self,
                "Atualizador GitHub",
                "O cliente de atualização automática via GitHub (Igorhls/vespera-sci) "
                "será conectado na Etapa 3.",
            )

    def _mostrar_sobre(self):
        QMessageBox.about(
            self,
            "Sobre o Vespera Sci",
            "<h3>Vespera Sci — Versão 1.0.0 (Beta)</h3>"
            "<p><b>Estúdio Científico de Análise de Dados e Gráficos</b></p>"
            "<p>Plataforma desktop científica para análise de dados experimentais, "
            "estatística descritiva e produção de figuras no padrão OriginLab Pro / ABNT.</p>"
            "<p>Repositório: <a href='https://github.com/Igorhls/vespera-sci'>"
            "github.com/Igorhls/vespera-sci</a></p>",
        )
