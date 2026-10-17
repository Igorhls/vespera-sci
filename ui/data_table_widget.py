"""
Widget de edição tabular de dados experimentais (Linhas P1..Pn e Barras TA).
Repaginação visual completa: ícones vetoriais SVG, sem emojis, abas modernas e altura total para a tabela.
"""

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.presets import PRESETS_BARRAS
from core.sanitizer import (
    calcular_estatisticas_serie,
    formatar_numero_ptbr,
    sanitizar_dados_barras,
    sanitizar_dados_tabela,
)
from ui.icons import get_icon


class DataTableWidget(QWidget):
    """Painel central moderno com abas separadas para dados, estatísticas e ferramentas."""

    dataOrMetaChanged = Signal()
    hideRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self.tipo_grafico = "linhas"
        self.setMinimumWidth(560)
        self.df_linhas = pd.DataFrame(columns=["Pontos", "Manha", "Tarde", "Noite"])
        self.df_barras = pd.DataFrame(
            columns=["Mes", "Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
        )

        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        # Sistema de Abas Principal da Área de Dados
        self.tabs = QTabWidget()
        self.btn_hide = QPushButton(" Ocultar")
        self.btn_hide.setIcon(get_icon("x", size=13))
        self.btn_hide.setToolTip("Ocultar Tabela de Dados (Ctrl+T)")
        self.btn_hide.setCursor(Qt.PointingHandCursor)
        self.btn_hide.clicked.connect(self.hideRequested.emit)
        self.tabs.setCornerWidget(self.btn_hide, Qt.TopRightCorner)

        root_layout.addWidget(self.tabs, stretch=1)

        # ===================================================================
        # ABA 1: Matriz de Dados (Tabela + Metadados Compactos)
        # ===================================================================
        tab_dados = QWidget()
        layout_dados = QVBoxLayout(tab_dados)
        layout_dados.setContentsMargins(8, 8, 8, 8)
        layout_dados.setSpacing(8)

        # 1. Card Superior Compacto de Metadados
        meta_card = QFrame()
        meta_card.setObjectName("cardPanel")
        grid_meta = QGridLayout(meta_card)
        grid_meta.setContentsMargins(10, 8, 10, 8)
        grid_meta.setHorizontalSpacing(8)
        grid_meta.setVerticalSpacing(6)

        self.lbl_tit_dia = QLabel("<b>Identificador / Dia:</b>")
        self.txt_titulo_dia = QLineEdit()
        self.txt_titulo_dia.setPlaceholderText("Ex: Dia 14 de Agosto")
        self.txt_titulo_dia.textChanged.connect(self._on_meta_changed)

        self.lbl_tit_graf = QLabel("<b>Título no Gráfico:</b>")
        self.txt_titulo_grafico = QLineEdit()
        self.txt_titulo_grafico.setPlaceholderText("Opcional (vazio = sem título)")
        self.txt_titulo_grafico.textChanged.connect(self._on_meta_changed)

        grid_meta.addWidget(self.lbl_tit_dia, 0, 0)
        grid_meta.addWidget(self.txt_titulo_dia, 0, 1)
        grid_meta.addWidget(self.lbl_tit_graf, 0, 2)
        grid_meta.addWidget(self.txt_titulo_grafico, 0, 3)

        self.txt_rotulo_x = QLineEdit()
        self.txt_rotulo_x.setPlaceholderText("Texto abaixo do eixo X (ou vazio)")
        self.txt_rotulo_x.textChanged.connect(self._on_meta_changed)
        self.txt_rotulo_y = QLineEdit()
        self.txt_rotulo_y.setPlaceholderText("Texto ao lado do eixo Y (ex: Ta (°C))")
        self.txt_rotulo_y.textChanged.connect(self._on_meta_changed)

        grid_meta.addWidget(QLabel("<b>Eixo X (Abaixo):</b>"), 1, 0)
        grid_meta.addWidget(self.txt_rotulo_x, 1, 1)
        grid_meta.addWidget(QLabel("<b>Eixo Y (Ao Lado):</b>"), 1, 2)
        grid_meta.addWidget(self.txt_rotulo_y, 1, 3)

        self.spn_min_y = QDoubleSpinBox()
        self.spn_min_y.setRange(-100.0, 500.0)
        self.spn_min_y.setDecimals(1)
        self.spn_min_y.setSingleStep(1.0)
        self.spn_min_y.valueChanged.connect(self._on_meta_changed)

        self.spn_max_y = QDoubleSpinBox()
        self.spn_max_y.setRange(-100.0, 500.0)
        self.spn_max_y.setDecimals(1)
        self.spn_max_y.setSingleStep(1.0)
        self.spn_max_y.valueChanged.connect(self._on_meta_changed)

        self.spn_intervalo_ticks_y = QDoubleSpinBox()
        self.spn_intervalo_ticks_y.setRange(0.0, 100.0)
        self.spn_intervalo_ticks_y.setDecimals(1)
        self.spn_intervalo_ticks_y.setSingleStep(1.0)
        self.spn_intervalo_ticks_y.setValue(0.0)
        self.spn_intervalo_ticks_y.setSpecialValueText("Automático")
        self.spn_intervalo_ticks_y.setToolTip("Espaçamento dos números/ticks no eixo Y (0 = Automático).")
        self.spn_intervalo_ticks_y.valueChanged.connect(self._on_meta_changed)

        grid_meta.addWidget(QLabel("<b>Limites Y:</b>"), 2, 0)
        lim_y_layout = QHBoxLayout()
        lim_y_layout.setContentsMargins(0, 0, 0, 0)
        lim_y_layout.setSpacing(6)
        lim_y_layout.addWidget(QLabel("Mín:"))
        lim_y_layout.addWidget(self.spn_min_y)
        lim_y_layout.addWidget(QLabel("Máx:"))
        lim_y_layout.addWidget(self.spn_max_y)
        grid_meta.addLayout(lim_y_layout, 2, 1)

        grid_meta.addWidget(QLabel("<b>Passo Ticks (Y):</b>"), 2, 2)
        grid_meta.addWidget(self.spn_intervalo_ticks_y, 2, 3)

        layout_dados.addWidget(meta_card)

        # 2. Configuração de nomes das séries em Modo Barras
        self.grp_rotulos_barras = QFrame()
        self.grp_rotulos_barras.setObjectName("cardPanel")
        rb_layout = QHBoxLayout(self.grp_rotulos_barras)
        rb_layout.setContentsMargins(10, 6, 10, 6)
        rb_layout.setSpacing(6)

        rb_layout.addWidget(QLabel("<b>Séries:</b>"))
        self.txt_rs1 = QLineEdit("Bosque")
        self.txt_rs2 = QLineEdit("Desvio/p")
        self.txt_rs3 = QLineEdit("Estacionamento")
        self.txt_rs4 = QLineEdit("Desvio/p")

        for lbl_t, w_edit in [
            ("S1:", self.txt_rs1),
            ("S2:", self.txt_rs2),
            ("S3:", self.txt_rs3),
            ("S4:", self.txt_rs4),
        ]:
            rb_layout.addWidget(QLabel(lbl_t))
            rb_layout.addWidget(w_edit)
            w_edit.textChanged.connect(self._on_rotulos_barras_changed)

        rb_layout.addSpacing(6)
        rb_layout.addWidget(QLabel("<b>Espaço Pares:</b>"))
        self.spn_espaco_subgrupos = QDoubleSpinBox()
        self.spn_espaco_subgrupos.setRange(0.0, 1.50)
        self.spn_espaco_subgrupos.setSingleStep(0.05)
        self.spn_espaco_subgrupos.setDecimals(2)
        self.spn_espaco_subgrupos.setValue(0.35)
        self.spn_espaco_subgrupos.setToolTip(
            "Espaçamento entre os pares/subgrupos de barras (ex: entre Bosque e Estacionamento)."
        )
        self.spn_espaco_subgrupos.valueChanged.connect(self._on_meta_changed)
        rb_layout.addWidget(self.spn_espaco_subgrupos)

        self.grp_rotulos_barras.setVisible(False)
        layout_dados.addWidget(self.grp_rotulos_barras)

        # 3. Barra de Ferramentas da Tabela com Ícones Vetoriais
        hl_table_btns = QHBoxLayout()
        hl_table_btns.setSpacing(6)

        self.btn_add_row = QPushButton("Linha")
        self.btn_add_row.setIcon(get_icon("plus", size=15))
        self.btn_add_row.setCursor(Qt.PointingHandCursor)
        self.btn_add_row.clicked.connect(self._adicionar_linha)

        self.btn_del_row = QPushButton("Remover")
        self.btn_del_row.setIcon(get_icon("minus", size=15))
        self.btn_del_row.setCursor(Qt.PointingHandCursor)
        self.btn_del_row.clicked.connect(self._remover_linha)

        self.btn_renum = QPushButton("Renumerar")
        self.btn_renum.setIcon(get_icon("hash", size=15))
        self.btn_renum.setCursor(Qt.PointingHandCursor)
        self.btn_renum.clicked.connect(self._renumerar_pontos)

        self.btn_padronizar = QPushButton("Padronizar")
        self.btn_padronizar.setIcon(get_icon("wand", size=15))
        self.btn_padronizar.setCursor(Qt.PointingHandCursor)
        self.btn_padronizar.clicked.connect(self._padronizar_decimais)

        self.btn_ir_colar = QPushButton("Colar do Excel")
        self.btn_ir_colar.setIcon(get_icon("clipboard", size=15))
        self.btn_ir_colar.setObjectName("btnPrimary")
        self.btn_ir_colar.setCursor(Qt.PointingHandCursor)
        self.btn_ir_colar.clicked.connect(lambda: self.tabs.setCurrentIndex(3))

        hl_table_btns.addWidget(self.btn_add_row)
        hl_table_btns.addWidget(self.btn_del_row)
        hl_table_btns.addWidget(self.btn_renum)
        hl_table_btns.addWidget(self.btn_padronizar)
        hl_table_btns.addStretch()
        hl_table_btns.addWidget(self.btn_ir_colar)

        layout_dados.addLayout(hl_table_btns)

        # 4. Tabela de Dados Principal (Altura total desimpedida)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemChanged.connect(self._on_table_item_changed)
        layout_dados.addWidget(self.table, stretch=1)

        self.tabs.addTab(tab_dados, get_icon("table", size=16), "Matriz de Dados")

        # ===================================================================
        # ABA 2: Resumo Estatístico Descritivo
        # ===================================================================
        tab_stats = QWidget()
        layout_stats = QVBoxLayout(tab_stats)
        layout_stats.setContentsMargins(12, 12, 12, 12)
        layout_stats.setSpacing(10)

        lbl_stats_head = QLabel("<b>Sumário Estatístico Descritivo das Medições</b>")
        lbl_stats_head.setStyleSheet("font-size: 14px;")
        layout_stats.addWidget(lbl_stats_head)

        lbl_stats_sub = QLabel(
            "Métricas calculadas em tempo real com base nos valores preenchidos na matriz de dados."
        )
        lbl_stats_sub.setStyleSheet("color: #64748b; font-size: 11.5px;")
        layout_stats.addWidget(lbl_stats_sub)

        self.card_stats_container = QFrame()
        self.card_stats_container.setObjectName("cardPanel")
        stats_box_layout = QVBoxLayout(self.card_stats_container)
        stats_box_layout.setContentsMargins(14, 14, 14, 14)

        self.lbl_stats = QLabel("Sem dados numéricos na tabela.")
        self.lbl_stats.setWordWrap(True)
        self.lbl_stats.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_stats.setStyleSheet("font-size: 13px; line-height: 1.6;")
        stats_box_layout.addWidget(self.lbl_stats)

        layout_stats.addWidget(self.card_stats_container)

        btn_copiar_stats = QPushButton("Copiar Resumo para Área de Transferência")
        btn_copiar_stats.setIcon(get_icon("clipboard", size=16))
        btn_copiar_stats.setCursor(Qt.PointingHandCursor)
        btn_copiar_stats.clicked.connect(self._copiar_resumo_estatistico)
        layout_stats.addWidget(btn_copiar_stats)

        layout_stats.addStretch()
        self.tabs.addTab(tab_stats, get_icon("activity", size=16), "Resumo Estatístico")

        # ===================================================================
        # ABA 3: Calculadora Rápida
        # ===================================================================
        tab_calc = QWidget()
        layout_calc = QVBoxLayout(tab_calc)
        layout_calc.setContentsMargins(12, 12, 12, 12)
        layout_calc.setSpacing(10)

        lbl_calc_head = QLabel("<b>Calculadora de Média e Desvio Padrão Amostral</b>")
        lbl_calc_head.setStyleSheet("font-size: 14px;")
        layout_calc.addWidget(lbl_calc_head)

        lbl_calc_sub = QLabel(
            "Digite ou cole números avulsos separados por espaço, vírgula ou ponto-e-vírgula para obter Média e Desvio Padrão (s)."
        )
        lbl_calc_sub.setWordWrap(True)
        lbl_calc_sub.setStyleSheet("color: #64748b; font-size: 11.5px;")
        layout_calc.addWidget(lbl_calc_sub)

        self.txt_calc_input = QLineEdit()
        self.txt_calc_input.setPlaceholderText("Ex: 26,2 26,5 26,9 27,2 27,4 27,1")
        self.txt_calc_input.setMinimumHeight(34)
        self.txt_calc_input.textChanged.connect(self._atualizar_calculadora)
        layout_calc.addWidget(self.txt_calc_input)

        calc_result_card = QFrame()
        calc_result_card.setObjectName("cardPanel")
        crc_layout = QVBoxLayout(calc_result_card)
        crc_layout.setContentsMargins(14, 14, 14, 14)

        self.lbl_calc_result = QLabel("Digite ao menos 2 valores acima para calcular.")
        self.lbl_calc_result.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.lbl_calc_result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        crc_layout.addWidget(self.lbl_calc_result)
        layout_calc.addWidget(calc_result_card)

        layout_calc.addStretch()
        self.tabs.addTab(tab_calc, get_icon("calculator", size=16), "Calculadora Rápida")

        # ===================================================================
        # ABA 4: Importador Direto do Excel
        # ===================================================================
        tab_paste = QWidget()
        layout_paste = QVBoxLayout(tab_paste)
        layout_paste.setContentsMargins(12, 12, 12, 12)
        layout_paste.setSpacing(10)

        lbl_paste_head = QLabel("<b>Importar Bloco de Dados do Excel (Ctrl+C ➔ Ctrl+V)</b>")
        lbl_paste_head.setStyleSheet("font-size: 14px;")
        layout_paste.addWidget(lbl_paste_head)

        lbl_paste_sub = QLabel(
            "Selecione uma faixa de células no Excel, pressione Ctrl+C e cole abaixo. "
            "Vírgulas decimais brasileiras e números inteiros colados são corrigidos automaticamente."
        )
        lbl_paste_sub.setWordWrap(True)
        lbl_paste_sub.setStyleSheet("color: #64748b; font-size: 11.5px;")
        layout_paste.addWidget(lbl_paste_sub)

        hl_dest = QHBoxLayout()
        self.lbl_destino = QLabel("<b>Destino das Colunas:</b>")
        self.cmb_destino_colar = QComboBox()
        self.cmb_destino_colar.addItems([
            "Apenas Manhã",
            "Apenas Tarde",
            "Apenas Noite",
            "Manhã, Tarde e Noite (3 colunas)",
            "Tabela Completa (Pontos + 3 colunas)",
        ])
        hl_dest.addWidget(self.lbl_destino)
        hl_dest.addWidget(self.cmb_destino_colar, stretch=1)
        layout_paste.addLayout(hl_dest)

        self.txt_paste = QPlainTextEdit()
        self.txt_paste.setPlaceholderText("Cole aqui os dados copiados do Excel (Ctrl+V)...")
        self.txt_paste.setMinimumHeight(150)
        layout_paste.addWidget(self.txt_paste, stretch=1)

        btn_aplicar_paste = QPushButton("Aplicar Dados na Tabela Principal")
        btn_aplicar_paste.setIcon(get_icon("check", color="#ffffff", size=16))
        btn_aplicar_paste.setObjectName("btnSuccess")
        btn_aplicar_paste.setCursor(Qt.PointingHandCursor)
        btn_aplicar_paste.setMinimumHeight(36)
        btn_aplicar_paste.clicked.connect(self._aplicar_colagem_excel)
        layout_paste.addWidget(btn_aplicar_paste)

        self.tabs.addTab(tab_paste, get_icon("clipboard", size=16), "Colar do Excel")

        # Rótulos para compatibilidade legada
        self.lbl_secao = QLabel()
        self.btn_toggle_paste = QPushButton()
        self.grp_paste = QWidget()

    def _copiar_resumo_estatistico(self):
        txt = self.lbl_stats.text().replace("<br>", "\n").replace("<b>", "").replace("</b>", "").replace("&nbsp;", " ")
        QApplication.clipboard().setText(txt)

    def _toggle_paste_box(self, checked: bool):
        self.tabs.setCurrentIndex(3 if checked else 0)

    def configurar_modo(self, tipo_grafico: str):
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        is_linhas = tipo_grafico == "linhas"

        self.grp_rotulos_barras.setVisible(not is_linhas)
        self.lbl_destino.setVisible(is_linhas)
        self.cmb_destino_colar.setVisible(is_linhas)

        if is_linhas:
            self.lbl_tit_dia.setText("<b>Identificador / Dia:</b>")
            self.btn_renum.setText("Renumerar")
            self.txt_paste.setPlaceholderText("Cole aqui os dados copiados do Excel...")
        else:
            self.lbl_tit_dia.setText("<b>Cabeçalho / Variável:</b>")
            self.btn_renum.setText("Restaurar Modelo TA")
            self.txt_paste.setPlaceholderText(
                "Agosto\t27,32\t2,3\t28,5\t4,87\nDezembro\t28,6\t1,42\t29,4\t2,19"
            )

        self._updating_ui = False
        self._popular_tabela()
        self.atualizar_sumario_estatistico()

    def carregar_dados_e_meta(
        self,
        tipo_grafico: str,
        df: pd.DataFrame,
        titulo_dia: str,
        titulo_grafico: str,
        min_y: float,
        max_y: float,
        cfg: dict,
    ):
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        if tipo_grafico == "linhas":
            self.df_linhas = df.copy()
        else:
            self.df_barras = df.copy()

        self.txt_titulo_dia.setText(str(titulo_dia or ""))
        self.txt_titulo_grafico.setText(str(titulo_grafico or ""))
        self.txt_rotulo_x.setText(str(cfg.get("rotulo_x", "Pontos")))
        self.txt_rotulo_y.setText(str(cfg.get("rotulo_y", "Temperatura do ar (°C)")))
        self.spn_min_y.setValue(float(min_y if min_y is not None else 24.0))
        self.spn_max_y.setValue(float(max_y if max_y is not None else 33.0))
        self.spn_intervalo_ticks_y.setValue(float(cfg.get("intervalo_ticks_y", 0.0)))

        self.txt_rs1.setText(str(cfg.get("rotulo_s1", "Bosque")))
        self.txt_rs2.setText(str(cfg.get("rotulo_s2", "Desvio/p")))
        self.txt_rs3.setText(str(cfg.get("rotulo_s3", "Estacionamento")))
        self.txt_rs4.setText(str(cfg.get("rotulo_s4", "Desvio/p")))
        self.spn_espaco_subgrupos.setValue(float(cfg.get("espaco_subgrupos_barras", 0.35)))
        self._updating_ui = False

        self.configurar_modo(tipo_grafico)

    def _popular_tabela(self):
        self._updating_ui = True
        self.table.clear()

        if self.tipo_grafico == "linhas":
            df = self.df_linhas
            colunas_internas = ["Pontos", "Manha", "Tarde", "Noite"]
            cabecalhos = ["Pontos", "Manhã (°C)", "Tarde (°C)", "Noite (°C)"]
            fmt_dec = "{:.1f}"
        else:
            df = self.df_barras
            colunas_internas = ["Mes", "Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
            cabecalhos = [
                "Mês",
                self.txt_rs1.text() or "Bosque",
                self.txt_rs2.text() or "Desvio/p",
                self.txt_rs3.text() or "Estacionamento",
                self.txt_rs4.text() or "Desvio/p",
            ]
            fmt_dec = "{:.2f}"

        self.table.setColumnCount(len(colunas_internas))
        self.table.setHorizontalHeaderLabels(cabecalhos)
        self.table.setRowCount(len(df))

        for r_idx in range(len(df)):
            for c_idx, col_name in enumerate(colunas_internas):
                val = df.iloc[r_idx].get(col_name, "")
                if c_idx == 0:
                    texto = "" if pd.isna(val) else str(val)
                else:
                    if pd.isna(val) or val == "":
                        texto = ""
                    else:
                        try:
                            texto = fmt_dec.format(float(val)).replace(".", ",")
                        except (ValueError, TypeError):
                            texto = str(val)
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r_idx, c_idx, item)

        self._updating_ui = False

    def _ler_dataframe_da_tabela(self) -> pd.DataFrame:
        rows = self.table.rowCount()
        if self.tipo_grafico == "linhas":
            colunas = ["Pontos", "Manha", "Tarde", "Noite"]
        else:
            colunas = ["Mes", "Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]

        dados = []
        for r in range(rows):
            linha = {}
            for c, col_name in enumerate(colunas):
                item = self.table.item(r, c)
                txt = item.text().strip() if item else ""
                if c == 0:
                    linha[col_name] = txt or (f"P{r+1}" if self.tipo_grafico == "linhas" else f"Mês {r+1}")
                else:
                    if not txt:
                        linha[col_name] = np.nan
                    else:
                        try:
                            linha[col_name] = float(txt.replace(",", "."))
                        except ValueError:
                            linha[col_name] = np.nan
            dados.append(linha)

        df_lido = pd.DataFrame(dados, columns=colunas)
        if self.tipo_grafico == "linhas":
            df_san, _ = sanitizar_dados_tabela(df_lido)
            self.df_linhas = df_san
            return df_san
        else:
            df_san, _ = sanitizar_dados_barras(df_lido)
            self.df_barras = df_san
            return df_san

    def obter_dataframe_atual(self) -> pd.DataFrame:
        return self.df_linhas.copy() if self.tipo_grafico == "linhas" else self.df_barras.copy()

    def obter_metadados(self) -> dict:
        return {
            "titulo_dia": self.txt_titulo_dia.text(),
            "titulo_grafico": self.txt_titulo_grafico.text(),
            "rotulo_x": self.txt_rotulo_x.text(),
            "rotulo_y": self.txt_rotulo_y.text(),
            "min_y": float(self.spn_min_y.value()),
            "max_y": float(self.spn_max_y.value()),
            "intervalo_ticks_y": float(self.spn_intervalo_ticks_y.value()),
            "rotulo_s1": self.txt_rs1.text() or "Bosque",
            "rotulo_s2": self.txt_rs2.text() or "Desvio/p",
            "rotulo_s3": self.txt_rs3.text() or "Estacionamento",
            "rotulo_s4": self.txt_rs4.text() or "Desvio/p",
            "espaco_subgrupos_barras": float(self.spn_espaco_subgrupos.value()),
        }

    def _on_table_item_changed(self, _item):
        if self._updating_ui:
            return
        self._ler_dataframe_da_tabela()
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()

    def _on_meta_changed(self):
        if not self._updating_ui:
            self.dataOrMetaChanged.emit()

    def _on_rotulos_barras_changed(self):
        if self._updating_ui:
            return
        if self.tipo_grafico == "barras":
            self.table.setHorizontalHeaderLabels([
                "Mês",
                self.txt_rs1.text() or "Bosque",
                self.txt_rs2.text() or "Desvio/p",
                self.txt_rs3.text() or "Estacionamento",
                self.txt_rs4.text() or "Desvio/p",
            ])
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()

    def _adicionar_linha(self):
        df = self._ler_dataframe_da_tabela()
        if self.tipo_grafico == "linhas":
            novo = pd.DataFrame(
                [{"Pontos": f"P{len(df)+1}", "Manha": 25.0, "Tarde": 29.0, "Noite": 26.0}]
            )
            self.df_linhas = pd.concat([df, novo], ignore_index=True)
        else:
            novo = pd.DataFrame([
                {
                    "Mes": f"Mês {len(df)+1}",
                    "Bosque": 27.0,
                    "Desvio_Bosque": 2.0,
                    "Estacionamento": 28.0,
                    "Desvio_Estacionamento": 3.0,
                }
            ])
            self.df_barras = pd.concat([df, novo], ignore_index=True)

        self._popular_tabela()
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()

    def _remover_linha(self):
        row = self.table.currentRow()
        df = self._ler_dataframe_da_tabela()
        if len(df) <= 1:
            return
        idx_remover = row if row >= 0 else len(df) - 1
        df_novo = df.drop(df.index[idx_remover]).reset_index(drop=True)
        if self.tipo_grafico == "linhas":
            self.df_linhas = df_novo
        else:
            self.df_barras = df_novo

        self._popular_tabela()
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()

    def _renumerar_pontos(self):
        if self.tipo_grafico == "linhas":
            df = self._ler_dataframe_da_tabela()
            df["Pontos"] = [f"P{i+1}" for i in range(len(df))]
            self.df_linhas = df
        else:
            self.df_barras = PRESETS_BARRAS["TA — Média e Desvio Padrão (Agosto e Dezembro)"]["df"].copy()
            self.spn_min_y.setValue(0.0)
            self.spn_max_y.setValue(35.0)

        self._popular_tabela()
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()

    def _padronizar_decimais(self):
        self._ler_dataframe_da_tabela()
        self._popular_tabela()
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()

    def _aplicar_colagem_excel(self):
        texto = self.txt_paste.toPlainText().strip()
        if not texto:
            return
        linhas_raw = [l.strip() for l in texto.split("\n") if l.strip()]

        if self.tipo_grafico == "linhas":
            destino = self.cmb_destino_colar.currentText()
            df_temp = self.df_linhas.copy()

            if destino in ["Apenas Manhã", "Apenas Tarde", "Apenas Noite"]:
                col_alvo = "Manha" if "Manhã" in destino else ("Tarde" if "Tarde" in destino else "Noite")
                valores = []
                for l in linhas_raw:
                    val_str = l.replace(",", ".").strip()
                    try:
                        v = float(val_str)
                        if 60.0 < v <= 600.0:
                            v = v / 10.0
                        valores.append(v)
                    except ValueError:
                        valores.append(np.nan)

                if len(valores) > len(df_temp):
                    linhas_extras = len(valores) - len(df_temp)
                    novos_pontos = [f"P{len(df_temp) + i + 1}" for i in range(linhas_extras)]
                    df_extra = pd.DataFrame({
                        "Pontos": novos_pontos,
                        "Manha": [np.nan] * linhas_extras,
                        "Tarde": [np.nan] * linhas_extras,
                        "Noite": [np.nan] * linhas_extras,
                    })
                    df_temp = pd.concat([df_temp, df_extra], ignore_index=True)

                for i, v in enumerate(valores):
                    df_temp.at[i, col_alvo] = v

            elif destino == "Manhã, Tarde e Noite (3 colunas)":
                novas_linhas = []
                for l in linhas_raw:
                    partes = [p.strip().replace(",", ".") for p in l.replace(";", "\t").split("\t")]
                    nums = []
                    for p in partes[:3]:
                        try:
                            v = float(p)
                            if 60.0 < v <= 600.0:
                                v = v / 10.0
                            nums.append(v)
                        except ValueError:
                            nums.append(np.nan)
                    while len(nums) < 3:
                        nums.append(np.nan)
                    novas_linhas.append(nums)
                df_temp = pd.DataFrame(novas_linhas, columns=["Manha", "Tarde", "Noite"])
                df_temp.insert(0, "Pontos", [f"P{i+1}" for i in range(len(df_temp))])

            else:
                novas_linhas = []
                for l in linhas_raw:
                    partes = [p.strip().replace(",", ".") for p in l.replace(";", "\t").split("\t")]
                    ponto_nome = partes[0]
                    nums = []
                    for p in partes[1:4]:
                        try:
                            v = float(p)
                            if 60.0 < v <= 600.0:
                                v = v / 10.0
                            nums.append(v)
                        except ValueError:
                            nums.append(np.nan)
                    while len(nums) < 3:
                        nums.append(np.nan)
                    novas_linhas.append([ponto_nome] + nums)
                df_temp = pd.DataFrame(novas_linhas, columns=["Pontos", "Manha", "Tarde", "Noite"])

            self.df_linhas, _ = sanitizar_dados_tabela(df_temp)

        else:
            novas_b = []
            for l in linhas_raw:
                partes = [p.strip().replace(",", ".") for p in l.replace(";", "\t").split("\t")]
                if len(partes) >= 5:
                    mes_nome = partes[0]
                    vals_num = partes[1:5]
                elif len(partes) == 4:
                    mes_nome = f"Mês {len(novas_b) + 1}"
                    vals_num = partes[:4]
                else:
                    continue
                nums = []
                for p in vals_num:
                    try:
                        nums.append(float(p))
                    except ValueError:
                        nums.append(np.nan)
                while len(nums) < 4:
                    nums.append(np.nan)
                novas_b.append([mes_nome] + nums)

            if novas_b:
                df_b = pd.DataFrame(
                    novas_b,
                    columns=["Mes", "Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"],
                )
                self.df_barras, _ = sanitizar_dados_barras(df_b)

        self._popular_tabela()
        self.atualizar_sumario_estatistico()
        self.dataOrMetaChanged.emit()
        self.tabs.setCurrentIndex(0)

    def _atualizar_calculadora(self, texto: str):
        partes = [
            p.strip().replace(",", ".")
            for p in texto.replace(";", " ").replace("\t", " ").split(" ")
            if p.strip()
        ]
        nums = []
        for p in partes:
            try:
                nums.append(float(p))
            except ValueError:
                pass
        if len(nums) >= 2:
            est = calcular_estatisticas_serie(nums)
            self.lbl_calc_result.setText(
                f"<b>Média:</b> {formatar_numero_ptbr(est['media'])} &nbsp;|&nbsp; "
                f"<b>Desvio Padrão (s):</b> {formatar_numero_ptbr(est['desvio'])} &nbsp;|&nbsp; "
                f"<b>Mín:</b> {formatar_numero_ptbr(est['minimo'])} &nbsp;|&nbsp; "
                f"<b>Máx:</b> {formatar_numero_ptbr(est['maximo'])} &nbsp;|&nbsp; "
                f"<b>N:</b> {est['n']} medições"
            )
        else:
            self.lbl_calc_result.setText("Digite ao menos 2 valores acima para calcular Média e Desvio Padrão.")

    def atualizar_sumario_estatistico(self):
        if self.tipo_grafico == "linhas":
            blocos = []
            for per, label in [("Manha", "Manhã"), ("Tarde", "Tarde"), ("Noite", "Noite")]:
                if per in self.df_linhas.columns:
                    est = calcular_estatisticas_serie(self.df_linhas[per])
                    if est:
                        blocos.append(
                            f"<b>{label}:</b> Média = <b>{est['media']:.2f} °C</b> &nbsp;|&nbsp; "
                            f"Desvio (s) = <b>{est['desvio']:.2f} °C</b> &nbsp;|&nbsp; "
                            f"Mín = <b>{est['minimo']:.1f} °C</b> &nbsp;|&nbsp; Máx = <b>{est['maximo']:.1f} °C</b> &nbsp;|&nbsp; "
                            f"Amplitude = <b>{est['amplitude']:.1f} °C</b> (N={est['n']})"
                        )
            self.lbl_stats.setText("<br><br>".join(blocos) if blocos else "Sem dados numéricos na tabela.")
        else:
            linhas_txt = []
            r1 = self.txt_rs1.text() or "Bosque"
            r3 = self.txt_rs3.text() or "Estacionamento"
            for _, row in self.df_barras.iterrows():
                mes = row.get("Mes", "")
                vb = formatar_numero_ptbr(row.get("Bosque"))
                db = formatar_numero_ptbr(row.get("Desvio_Bosque"))
                ve = formatar_numero_ptbr(row.get("Estacionamento"))
                de = formatar_numero_ptbr(row.get("Desvio_Estacionamento"))
                linhas_txt.append(f"<b>{mes}:</b> {r1} = <b>{vb} (±{db})</b> &nbsp;|&nbsp; {r3} = <b>{ve} (±{de})</b>")
            self.lbl_stats.setText("<br><br>".join(linhas_txt) if linhas_txt else "Sem dados na tabela.")
