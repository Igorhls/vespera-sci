"""
Janela Principal (QMainWindow) do Vespera Sci Desktop.
Integra a Barra de Gerenciamento de Projetos, Barra Lateral de Estilo,
Editor Tabular de Dados e Canvas Interativo do Matplotlib.
"""

import json
import os
import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
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

from config.presets import PRESETS_BARRAS, PRESETS_LINHAS
from config.themes import DEFAULT_CONFIG
from core.excel_exporter import gerar_excel_barras_bytes, gerar_excel_linhas_bytes
from core.plot_engine import renderizar_grafico_barras, renderizar_grafico_linhas
from core.project_manager import ProjectManager
from ui.data_table_widget import DataTableWidget
from ui.plot_canvas_widget import PlotCanvasWidget
from ui.sidebar_controls import SidebarControlsWidget


class VesperaMainWindow(QMainWindow):
    """Janela principal do estúdio científico Vespera Sci."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vespera Sci — Scientific Plotting & Data Analysis Studio")
        self.resize(1440, 880)

        self.project_manager = ProjectManager()
        self.banco_projetos = self.project_manager.ler_banco()

        self.tipo_grafico_atual = "linhas"
        self.nome_projeto_atual = "Dia 14 de agosto"
        self.cfg_atual = DEFAULT_CONFIG.copy()
        self._updating_project_combo = False

        self._apply_stylesheet()
        self._build_menu()
        self._build_ui()
        self._inicializar_sessao()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                font-family: "Segoe UI", -apple-system, Arial, sans-serif;
                font-size: 12.5px;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QPushButton {
                border: 1px solid #c4c9d0;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton#btnPrimary {
                background-color: #1f5f8b;
                color: #ffffff;
                border: 1px solid #164666;
                font-weight: 600;
            }
            QPushButton#btnPrimary:hover {
                background-color: #184b6e;
            }
            QPushButton#btnUpdate {
                background-color: #216e39;
                color: #ffffff;
                border: 1px solid #19542b;
                font-weight: 600;
            }
            QPushButton#btnUpdate:hover {
                background-color: #19542b;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QPlainTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 6px;
                background-color: #ffffff;
            }
        """)

    def _build_menu(self):
        menubar = self.menuBar()

        menu_arq = menubar.addMenu("&Arquivo")

        act_salvar = QAction("💾 Salvar Projeto Atual", self)
        act_salvar.setShortcut(QKeySequence.Save)
        act_salvar.triggered.connect(self._salvar_projeto_atual)
        menu_arq.addAction(act_salvar)

        act_imp_json = QAction("📂 Importar Projeto (.json / .vespera)...", self)
        act_imp_json.triggered.connect(self._importar_arquivo_projeto)
        menu_arq.addAction(act_imp_json)

        act_imp_xlsx = QAction("📊 Importar Planilha (.xlsx / .csv)...", self)
        act_imp_xlsx.triggered.connect(self._importar_planilha)
        menu_arq.addAction(act_imp_xlsx)

        menu_arq.addSeparator()

        act_sair = QAction("Sair", self)
        act_sair.setShortcut(QKeySequence.Quit)
        act_sair.triggered.connect(self.close)
        menu_arq.addAction(act_sair)

        menu_ajuda = menubar.addMenu("A&juda")
        act_update = QAction("🔄 Verificar Atualizações no GitHub...", self)
        act_update.triggered.connect(self._acionar_verificacao_atualizacao)
        menu_ajuda.addAction(act_update)

        act_sobre = QAction("ℹ️ Sobre o Vespera Sci", self)
        act_sobre.triggered.connect(self._mostrar_sobre)
        menu_ajuda.addAction(act_sobre)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(8)

        # -------------------------------------------------------------------
        # 1. Cabeçalho Institucional + Botão de Auto-Update
        # -------------------------------------------------------------------
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("🌌 <b>Vespera Sci</b> — Sistema de Análise Científica e Gráficos de Publicação")
        lbl_title.setStyleSheet("font-size: 18px;")
        lbl_sub = QLabel(
            "Estúdio Desktop de Monitoramento Térmico, Estatística Descritiva e Figuras Padrão OriginLab Pro"
        )
        lbl_sub.setStyleSheet("color: #555555; font-size: 12px;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_check_update = QPushButton("🔄 Verificar Atualizações (GitHub)")
        self.btn_check_update.setObjectName("btnUpdate")
        self.btn_check_update.setCursor(Qt.PointingHandCursor)
        self.btn_check_update.setMinimumHeight(34)
        self.btn_check_update.clicked.connect(self._acionar_verificacao_atualizacao)
        header_layout.addWidget(self.btn_check_update)

        root_layout.addLayout(header_layout)

        # -------------------------------------------------------------------
        # 2. Barra Superior de Salvamento e Gerenciamento de Projetos
        # -------------------------------------------------------------------
        proj_frame = QFrame()
        proj_frame.setFrameShape(QFrame.StyledPanel)
        proj_layout = QHBoxLayout(proj_frame)
        proj_layout.setContentsMargins(10, 6, 10, 6)
        proj_layout.setSpacing(8)

        proj_layout.addWidget(QLabel("📌 <b>Projeto:</b>"))
        self.txt_nome_projeto = QLineEdit()
        self.txt_nome_projeto.setPlaceholderText("Ex: Dia 14 de Agosto - Bosque")
        self.txt_nome_projeto.setMinimumWidth(210)
        proj_layout.addWidget(self.txt_nome_projeto)

        self.btn_salvar_proj = QPushButton("💾 Salvar Projeto (Ctrl+S)")
        self.btn_salvar_proj.setObjectName("btnPrimary")
        self.btn_salvar_proj.setCursor(Qt.PointingHandCursor)
        self.btn_salvar_proj.clicked.connect(self._salvar_projeto_atual)
        proj_layout.addWidget(self.btn_salvar_proj)

        proj_layout.addWidget(QLabel("📂 <b>Salvos:</b>"))
        self.cmb_projetos_salvos = QComboBox()
        self.cmb_projetos_salvos.setMinimumWidth(260)
        self.cmb_projetos_salvos.currentIndexChanged.connect(self._on_projeto_salvo_selecionado)
        proj_layout.addWidget(self.cmb_projetos_salvos, stretch=1)

        self.btn_exportar_json = QPushButton("📥 Baixar (.json)")
        self.btn_exportar_json.setCursor(Qt.PointingHandCursor)
        self.btn_exportar_json.clicked.connect(self._exportar_projeto_json)
        proj_layout.addWidget(self.btn_exportar_json)

        self.btn_excluir_proj = QPushButton("🗑️ Excluir")
        self.btn_excluir_proj.setCursor(Qt.PointingHandCursor)
        self.btn_excluir_proj.clicked.connect(self._excluir_projeto_atual)
        proj_layout.addWidget(self.btn_excluir_proj)

        root_layout.addWidget(proj_frame)

        # -------------------------------------------------------------------
        # 3. Seletores Rápidos de Modo
        # -------------------------------------------------------------------
        mode_bar = QHBoxLayout()
        self.btn_modo_linhas = QPushButton("📈 Gráfico de Linhas — Pontos Amostrais (Manhã, Tarde e Noite)")
        self.btn_modo_linhas.setCursor(Qt.PointingHandCursor)
        self.btn_modo_linhas.setMinimumHeight(32)
        self.btn_modo_linhas.clicked.connect(lambda: self._alternar_modo("linhas"))

        self.btn_modo_barras = QPushButton(
            "📊 Gráfico de Barras — Média e Desvio Padrão (Bosque vs. Estacionamento)"
        )
        self.btn_modo_barras.setCursor(Qt.PointingHandCursor)
        self.btn_modo_barras.setMinimumHeight(32)
        self.btn_modo_barras.clicked.connect(lambda: self._alternar_modo("barras"))

        mode_bar.addWidget(self.btn_modo_linhas)
        mode_bar.addWidget(self.btn_modo_barras)
        root_layout.addLayout(mode_bar)

        # -------------------------------------------------------------------
        # 4. Área Principal Dividida (Sidebar | Tabela | Gráfico)
        # -------------------------------------------------------------------
        splitter = QSplitter(Qt.Horizontal)

        self.sidebar = SidebarControlsWidget()
        self.table_widget = DataTableWidget()
        self.plot_widget = PlotCanvasWidget()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.table_widget)
        splitter.addWidget(self.plot_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([330, 520, 580])

        root_layout.addWidget(splitter, stretch=1)

        # Barra de status inferior
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Conexão de sinais
        self.sidebar.configChanged.connect(self.atualizar_grafico)
        self.sidebar.modeChangeRequested.connect(self._alternar_modo)
        self.sidebar.presetSelected.connect(self._carregar_preset)
        self.sidebar.importSpreadsheetRequested.connect(self._importar_planilha)
        self.sidebar.importProjectFileRequested.connect(self._importar_arquivo_projeto)

        self.table_widget.dataOrMetaChanged.connect(self.atualizar_grafico)
        self.plot_widget.seriesVisibilityChanged.connect(self.atualizar_grafico)
        self.plot_widget.exportExcelRequested.connect(self._exportar_planilha_excel)

    def _inicializar_sessao(self):
        self._atualizar_combo_projetos()
        ultimo = self.banco_projetos.get("ultimo_projeto_ativo")
        projetos_dict = self.banco_projetos.get("projetos", {})
        if ultimo and ultimo in projetos_dict:
            self._aplicar_projeto_dict(projetos_dict[ultimo])
            self.status_bar.showMessage(f"✅ Projeto '{ultimo}' restaurado automaticamente.")
        else:
            self._carregar_preset("Dia 14 de Agosto")
            self.status_bar.showMessage("💡 Pronto. Selecione um modelo ou edite os valores na tabela.")

    def _atualizar_botoes_modo(self):
        if self.tipo_grafico_atual == "linhas":
            self.btn_modo_linhas.setObjectName("btnPrimary")
            self.btn_modo_barras.setObjectName("")
        else:
            self.btn_modo_linhas.setObjectName("")
            self.btn_modo_barras.setObjectName("btnPrimary")
        self.style().unpolish(self.btn_modo_linhas)
        self.style().polish(self.btn_modo_linhas)
        self.style().unpolish(self.btn_modo_barras)
        self.style().polish(self.btn_modo_barras)

    def _alternar_modo(self, novo_modo: str):
        if novo_modo == self.tipo_grafico_atual:
            return
        if novo_modo == "barras":
            self._carregar_preset("TA — Média e Desvio Padrão (Agosto e Dezembro)")
        else:
            self._carregar_preset("Dia 14 de Agosto")

    def _carregar_preset(self, nome_preset: str):
        cfg = self.sidebar.obter_config()
        cfg.update(self.plot_widget.obter_estado_series())

        if nome_preset in PRESETS_BARRAS:
            p = PRESETS_BARRAS[nome_preset]
            self.tipo_grafico_atual = "barras"
            self.nome_projeto_atual = "TA - Média e Desvio Padrão"
            cfg["rotulo_x"] = p["rotulo_x"]
            cfg["rotulo_y"] = p["rotulo_y"]
            cfg["opcao_fonte"] = "Arial (Científico Internacional)"
            cfg["direcao_ticks"] = "Para fora (out)"
            cfg["ticks_topo"] = False
            cfg["ticks_dir"] = False
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

        titulo_dia = proj_dict.get("titulo_dia", "TA" if tipo == "barras" else "Dia 14 de agosto")
        titulo_grafico = proj_dict.get("titulo_grafico", "" if tipo == "barras" else "DIA 14 DE AGOSTO - BOSQUE")
        min_y = float(proj_dict.get("min_y", 0.0 if tipo == "barras" else 24.0))
        max_y = float(proj_dict.get("max_y", 35.0 if tipo == "barras" else 33.0))

        registros = proj_dict.get("dados", [])
        if tipo == "barras":
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

    def atualizar_grafico(self):
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
            estilos_linhas = (
                {"Manha": "-", "Tarde": "--", "Noite": ":"}
                if cfg["com_linhas_distintas"]
                else {"Manha": "-", "Tarde": "-", "Noite": "-"}
            )
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
                com_marcadores=cfg["com_marcadores"],
                bordas_config=bordas_config,
                ticks_config=ticks_config,
                legenda_config=legenda_config,
                exibir_grade=cfg["exibir_grade"],
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
        self.cmb_projetos_salvos.addItem(f"Selecione um projeto salvo ({len(projetos)})...", None)
        for nome, p in projetos.items():
            icone = "📊" if p.get("tipo_grafico") == "barras" else "📈"
            data_str = p.get("atualizado_em", "")
            self.cmb_projetos_salvos.addItem(f"{icone} {nome} ({data_str})", nome)
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
        self.status_bar.showMessage(f"💾 Projeto '{nome_final}' salvo com sucesso em {payload['atualizado_em']}.")

    def _on_projeto_salvo_selecionado(self, index: int):
        if self._updating_project_combo or index <= 0:
            return
        nome = self.cmb_projetos_salvos.itemData(index)
        projetos = self.banco_projetos.get("projetos", {})
        if nome and nome in projetos:
            self._aplicar_projeto_dict(projetos[nome])
            self.banco_projetos["ultimo_projeto_ativo"] = nome
            self.project_manager.gravar_banco(self.banco_projetos)
            self.status_bar.showMessage(f"📂 Projeto '{nome}' carregado com sucesso.")
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
            self.status_bar.showMessage(f"🗑️ Projeto '{alvo}' excluído.")

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
                self.status_bar.showMessage(f"📥 Backup do projeto salvo em: {caminho}")
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
                    self.status_bar.showMessage(f"✅ Projeto '{nome_imp}' importado e salvo!")
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
            if all(c in df_mapped.columns for c in cols_req):
                self.tipo_grafico_atual = "linhas"
                nome_base = os.path.splitext(os.path.basename(caminho))[0]
                self.nome_projeto_atual = nome_base
                self.txt_nome_projeto.setText(nome_base)
                cfg = self.sidebar.obter_config()
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
                self.status_bar.showMessage(f"✅ Planilha '{os.path.basename(caminho)}' importada com sucesso.")
            else:
                QMessageBox.warning(
                    self,
                    "Colunas Não Encontradas",
                    "A planilha deve conter as colunas: Pontos, Manha, Tarde e Noite.",
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
        """Gancho para o módulo de atualização via GitHub (implementado na Etapa 3)."""
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
            "<h3>🌌 Vespera Sci v1.0.0</h3>"
            "<p><b>Scientific Plotting & Data Analysis Studio</b></p>"
            "<p>Plataforma desktop científica para análise de dados experimentais, "
            "estatística descritiva e produção de figuras no padrão OriginLab Pro / ABNT.</p>"
            "<p>Repositório: <a href='https://github.com/Igorhls/vespera-sci'>"
            "github.com/Igorhls/vespera-sci</a></p>",
        )
