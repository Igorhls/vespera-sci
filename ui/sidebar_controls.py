"""
Painel lateral de configurações estéticas e controles estilo OriginLab Pro para o Vespera Sci.
Reorganizado em abas temáticas com ícones vetoriais SVG, sem emojis e sem cortes horizontais.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.presets import PRESETS_BARRAS, PRESETS_LINHAS
from config.themes import (
    COORDENADAS_LEGENDA_PRESET,
    DEFAULT_CONFIG,
    FONTES_DISPONIVEIS,
    MAPA_SIMBOLOS,
    MAPA_TRACOS,
    MODOS_ESTILO_LINHAS,
    PALETAS_BARRAS,
    PALETAS_LINHAS,
    POSICOES_LEGENDA,
)
from ui.icons import get_icon


class ColorButton(QPushButton):
    """Botão seletor de cor com indicador visual circular e tooltip informativo."""

    colorChanged = Signal(str)

    def __init__(self, hex_color: str = "#000000", label_prefix: str = "", parent=None):
        super().__init__(parent)
        self._label_prefix = label_prefix
        self._hex_color = hex_color
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(30)
        self.clicked.connect(self._pick_color)
        self._update_appearance()

    def set_color(self, hex_color: str):
        self._hex_color = hex_color
        self._update_appearance()

    def get_color(self) -> str:
        return self._hex_color

    def _update_appearance(self):
        pixmap = QPixmap(14, 14)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self._hex_color))
        painter.setPen(QColor("#64748b"))
        painter.drawEllipse(1, 1, 12, 12)
        painter.end()

        self.setIcon(QIcon(pixmap))
        texto = f"{self._label_prefix}" if self._label_prefix else self._hex_color
        self.setText(f"  {texto}")
        self.setToolTip(f"{texto}: {self._hex_color} (Clique para alterar)")
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 8px;
                font-weight: 600;
                border-radius: 6px;
            }
        """)

    def _pick_color(self):
        cor = QColorDialog.getColor(QColor(self._hex_color), self, f"Selecionar Cor — {self._label_prefix}")
        if cor.isValid():
            self._hex_color = cor.name()
            self._update_appearance()
            self.colorChanged.emit(self._hex_color)


class SidebarControlsWidget(QScrollArea):
    """Barra lateral rolável dividida em abas de estilo profissional."""

    configChanged = Signal()
    modeChangeRequested = Signal(str)
    presetSelected = Signal(str)
    importSpreadsheetRequested = Signal()
    importProjectFileRequested = Signal()
    hideRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self.tipo_grafico = "linhas"
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumWidth(340)

        self.container = QWidget()
        self.setWidget(self.container)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # -------------------------------------------------------------------
        # 1. Card Superior: Modelos Rápidos e Importação (Layout Vertical sem cortes)
        # -------------------------------------------------------------------
        top_card = QFrame()
        top_card.setObjectName("cardPanel")
        tc_layout = QVBoxLayout(top_card)
        tc_layout.setContentsMargins(10, 10, 10, 10)
        tc_layout.setSpacing(8)

        header_top = QHBoxLayout()
        header_top.setContentsMargins(0, 0, 0, 0)
        lbl_presets = QLabel("<b>Modelos e Presets</b>")
        header_top.addWidget(lbl_presets)
        header_top.addStretch()

        self.btn_hide = QPushButton(" Fechar")
        self.btn_hide.setIcon(get_icon("x", size=13))
        self.btn_hide.setToolTip("Fechar Submenu de Configurações")
        self.btn_hide.setCursor(Qt.PointingHandCursor)
        self.btn_hide.clicked.connect(self.hideRequested.emit)
        header_top.addWidget(self.btn_hide)

        tc_layout.addLayout(header_top)

        self.cmb_presets = QComboBox()
        opcoes_preset = (
            ["Carregar modelo pré-cadastrado..."]
            + list(PRESETS_LINHAS.keys())
            + list(PRESETS_BARRAS.keys())
            + ["Criar Novo — Linhas (Pontos P1–P10)", "Criar Novo — Barras (Média e Desvio)"]
        )
        self.cmb_presets.addItems(opcoes_preset)
        self.cmb_presets.currentIndexChanged.connect(self._on_preset_chosen)
        tc_layout.addWidget(self.cmb_presets)

        vl_imp = QVBoxLayout()
        vl_imp.setSpacing(6)

        btn_imp_xlsx = QPushButton("Importar Planilha (.xlsx / .csv)")
        btn_imp_xlsx.setIcon(get_icon("file-spreadsheet", size=16))
        btn_imp_xlsx.setCursor(Qt.PointingHandCursor)
        btn_imp_xlsx.clicked.connect(self.importSpreadsheetRequested.emit)

        btn_imp_json = QPushButton("Abrir Projeto (.json / .vespera)")
        btn_imp_json.setIcon(get_icon("folder", size=16))
        btn_imp_json.setCursor(Qt.PointingHandCursor)
        btn_imp_json.clicked.connect(self.importProjectFileRequested.emit)

        vl_imp.addWidget(btn_imp_xlsx)
        vl_imp.addWidget(btn_imp_json)
        tc_layout.addLayout(vl_imp)

        # Radio buttons ocultos para manter compatibilidade legada
        self.rb_linhas = QRadioButton("Linhas")
        self.rb_barras = QRadioButton("Barras")
        self.rb_linhas.setChecked(True)
        self.rb_linhas.toggled.connect(self._on_modo_toggled)

        main_layout.addWidget(top_card)

        # -------------------------------------------------------------------
        # 2. Abas de Customização Estética com Ícones Vetoriais
        # -------------------------------------------------------------------
        self.tab_estilos = QTabWidget()
        main_layout.addWidget(self.tab_estilos, stretch=1)

        # ABA 1: Tipografia & Traço
        tab_estilo = QWidget()
        l_estilo = QVBoxLayout(tab_estilo)
        l_estilo.setContentsMargins(6, 8, 6, 8)
        l_estilo.setSpacing(10)

        grp_font = QGroupBox("Tipografia Acadêmica (ABNT / OriginLab)")
        form_font = QFormLayout(grp_font)
        form_font.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_font.setLabelAlignment(Qt.AlignLeft)
        form_font.setHorizontalSpacing(8)
        form_font.setVerticalSpacing(8)

        self.cmb_fonte = QComboBox()
        self.cmb_fonte.addItems(FONTES_DISPONIVEIS)
        self.cmb_fonte.currentIndexChanged.connect(self._emit_change)

        self.spn_tam_fonte = QDoubleSpinBox()
        self.spn_tam_fonte.setRange(8.0, 18.0)
        self.spn_tam_fonte.setSingleStep(0.5)
        self.spn_tam_fonte.setValue(11.0)
        self.spn_tam_fonte.valueChanged.connect(self._emit_change)

        form_font.addRow("Família:", self.cmb_fonte)
        form_font.addRow("Tamanho (pt):", self.spn_tam_fonte)
        l_estilo.addWidget(grp_font)

        # Opções Linhas
        self.grp_opcoes_linhas = QGroupBox("Traços e Marcadores (Linhas)")
        ol_layout = QVBoxLayout(self.grp_opcoes_linhas)
        ol_layout.setSpacing(8)

        lbl_modo = QLabel("<b>Apresentação das Linhas:</b>")
        ol_layout.addWidget(lbl_modo)

        self.cmb_modo_linhas = QComboBox()
        self.cmb_modo_linhas.addItems(MODOS_ESTILO_LINHAS)
        self.cmb_modo_linhas.currentIndexChanged.connect(self._on_modo_linhas_changed)
        ol_layout.addWidget(self.cmb_modo_linhas)

        form_traco = QFormLayout()
        form_traco.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_traco.setLabelAlignment(Qt.AlignLeft)
        form_traco.setHorizontalSpacing(8)
        form_traco.setVerticalSpacing(6)

        self.spn_esp_linha = QDoubleSpinBox()
        self.spn_esp_linha.setRange(0.5, 5.0)
        self.spn_esp_linha.setSingleStep(0.1)
        self.spn_esp_linha.setValue(1.2)
        self.spn_esp_linha.valueChanged.connect(self._emit_change)

        self.lbl_tam_marcador = QLabel("Tamanho Símbolo (pt):")
        self.spn_tam_marcador = QDoubleSpinBox()
        self.spn_tam_marcador.setRange(2.0, 15.0)
        self.spn_tam_marcador.setSingleStep(0.5)
        self.spn_tam_marcador.setValue(6.0)
        self.spn_tam_marcador.valueChanged.connect(self._emit_change)

        form_traco.addRow("Espessura Linha (pt):", self.spn_esp_linha)
        form_traco.addRow(self.lbl_tam_marcador, self.spn_tam_marcador)
        ol_layout.addLayout(form_traco)

        self.chk_descritivo_legenda = QCheckBox("Exibir tipo na legenda (ex: Manhã (Bolinha))")
        self.chk_descritivo_legenda.setChecked(True)
        self.chk_descritivo_legenda.toggled.connect(self._emit_change)
        ol_layout.addWidget(self.chk_descritivo_legenda)

        self.chk_grade_estilo = QCheckBox("Exibir grade de fundo (Quadrados de apoio)")
        self.chk_grade_estilo.setChecked(True)
        self.chk_grade_estilo.toggled.connect(self._on_grade_estilo_toggled)
        ol_layout.addWidget(self.chk_grade_estilo)

        # Painel Retrátil para Customização Avançada por Série
        self.frame_custom_linhas = QFrame()
        self.frame_custom_linhas.setStyleSheet("QFrame { background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08); border-radius: 6px; padding: 4px; }")
        fl_custom = QVBoxLayout(self.frame_custom_linhas)
        fl_custom.setContentsMargins(6, 6, 6, 6)
        fl_custom.setSpacing(6)

        lbl_custom_tit = QLabel("<b>Ajuste Individual por Série:</b>")
        fl_custom.addWidget(lbl_custom_tit)

        grid_series = QGridLayout()
        grid_series.setHorizontalSpacing(6)
        grid_series.setVerticalSpacing(4)
        grid_series.addWidget(QLabel("<b>Série</b>"), 0, 0)
        grid_series.addWidget(QLabel("<b>Traçado</b>"), 0, 1)
        grid_series.addWidget(QLabel("<b>Marcador</b>"), 0, 2)

        self.cmb_traco_manha = QComboBox()
        self.cmb_traco_tarde = QComboBox()
        self.cmb_traco_noite = QComboBox()
        for cmb in (self.cmb_traco_manha, self.cmb_traco_tarde, self.cmb_traco_noite):
            for nome_t, cod_t in MAPA_TRACOS.items():
                cmb.addItem(nome_t, cod_t)
            cmb.currentIndexChanged.connect(self._emit_change)

        self.cmb_simbolo_manha = QComboBox()
        self.cmb_simbolo_tarde = QComboBox()
        self.cmb_simbolo_noite = QComboBox()
        for cmb in (self.cmb_simbolo_manha, self.cmb_simbolo_tarde, self.cmb_simbolo_noite):
            for nome_s, cod_s in MAPA_SIMBOLOS.items():
                cmb.addItem(nome_s, cod_s)
            cmb.currentIndexChanged.connect(self._emit_change)

        grid_series.addWidget(QLabel("Manhã:"), 1, 0)
        grid_series.addWidget(self.cmb_traco_manha, 1, 1)
        grid_series.addWidget(self.cmb_simbolo_manha, 1, 2)

        grid_series.addWidget(QLabel("Tarde:"), 2, 0)
        grid_series.addWidget(self.cmb_traco_tarde, 2, 1)
        grid_series.addWidget(self.cmb_simbolo_tarde, 2, 2)

        grid_series.addWidget(QLabel("Noite:"), 3, 0)
        grid_series.addWidget(self.cmb_traco_noite, 3, 1)
        grid_series.addWidget(self.cmb_simbolo_noite, 3, 2)

        fl_custom.addLayout(grid_series)
        self.frame_custom_linhas.setVisible(False)
        ol_layout.addWidget(self.frame_custom_linhas)

        # Checkboxes legados ocultos para retrocompatibilidade
        self.chk_marcadores = QCheckBox()
        self.chk_linhas_distintas = QCheckBox()

        l_estilo.addWidget(self.grp_opcoes_linhas)

        # Opções Barras
        self.grp_opcoes_barras = QGroupBox("Opções de Barras e Rótulos")
        ob_layout = QVBoxLayout(self.grp_opcoes_barras)
        ob_layout.setSpacing(6)

        self.chk_exibir_valores_barras = QCheckBox("Exibir valores sobre as barras")
        self.chk_exibir_valores_barras.setChecked(True)
        self.chk_negrito_barras = QCheckBox("Valores das barras em negrito")
        self.chk_negrito_barras.setChecked(True)
        for chk in (self.chk_exibir_valores_barras, self.chk_negrito_barras):
            chk.toggled.connect(self._emit_change)
            ob_layout.addWidget(chk)

        form_barras = QFormLayout()
        form_barras.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_barras.setLabelAlignment(Qt.AlignLeft)
        form_barras.setHorizontalSpacing(8)
        form_barras.setVerticalSpacing(6)

        self.cmb_fmt_decimais = QComboBox()
        self.cmb_fmt_decimais.addItems([
            "Automático (ex: 27,32 | 2,3)",
            "2 Casas Decimais Fixas (ex: 27,32 | 2,30)",
        ])
        self.cmb_fmt_decimais.currentIndexChanged.connect(self._emit_change)

        self.spn_largura_grupo = QDoubleSpinBox()
        self.spn_largura_grupo.setRange(0.30, 0.95)
        self.spn_largura_grupo.setSingleStep(0.02)
        self.spn_largura_grupo.setValue(0.68)
        self.spn_largura_grupo.valueChanged.connect(self._emit_change)

        form_barras.addRow("Formato:", self.cmb_fmt_decimais)
        form_barras.addRow("Largura:", self.spn_largura_grupo)
        ob_layout.addLayout(form_barras)
        self.grp_opcoes_barras.setVisible(False)
        l_estilo.addWidget(self.grp_opcoes_barras)

        l_estilo.addStretch()
        self.tab_estilos.addTab(tab_estilo, get_icon("type", size=15), "Estilo")

        # ABA 2: Eixos & Quadro
        tab_eixos = QWidget()
        l_eixos = QVBoxLayout(tab_eixos)
        l_eixos.setContentsMargins(6, 8, 6, 8)
        l_eixos.setSpacing(10)

        grp_bordas = QGroupBox("Bordas do Quadro")
        grid_b = QGridLayout(grp_bordas)
        grid_b.setHorizontalSpacing(8)
        grid_b.setVerticalSpacing(6)
        self.chk_b_top = QCheckBox("Superior")
        self.chk_b_bot = QCheckBox("Inferior")
        self.chk_b_left = QCheckBox("Esquerda")
        self.chk_b_right = QCheckBox("Direita")
        for idx, chk in enumerate((self.chk_b_top, self.chk_b_bot, self.chk_b_left, self.chk_b_right)):
            chk.setChecked(True)
            chk.toggled.connect(self._emit_change)
            grid_b.addWidget(chk, idx // 2, idx % 2)
        l_eixos.addWidget(grp_bordas)

        grp_ticks = QGroupBox("Traços de Escala (Ticks)")
        l_gticks = QVBoxLayout(grp_ticks)
        l_gticks.setSpacing(6)

        grid_t = QGridLayout()
        grid_t.setHorizontalSpacing(8)
        grid_t.setVerticalSpacing(6)
        self.chk_t_top = QCheckBox("Topo")
        self.chk_t_bot = QCheckBox("Base")
        self.chk_t_left = QCheckBox("Esquerda")
        self.chk_t_right = QCheckBox("Direita")
        for idx, chk in enumerate((self.chk_t_top, self.chk_t_bot, self.chk_t_left, self.chk_t_right)):
            chk.setChecked(True)
            chk.toggled.connect(self._emit_change)
            grid_t.addWidget(chk, idx // 2, idx % 2)
        l_gticks.addLayout(grid_t)

        self.chk_minor_ticks = QCheckBox("Exibir subtraços (Minor Ticks)")
        self.chk_minor_ticks.setChecked(True)
        self.chk_minor_ticks.toggled.connect(self._emit_change)
        l_gticks.addWidget(self.chk_minor_ticks)

        form_ticks = QFormLayout()
        form_ticks.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_ticks.setLabelAlignment(Qt.AlignLeft)
        form_ticks.setHorizontalSpacing(8)
        form_ticks.setVerticalSpacing(6)

        self.cmb_dir_ticks = QComboBox()
        self.cmb_dir_ticks.addItems(["Para dentro (in)", "Para fora (out)"])
        self.cmb_dir_ticks.currentIndexChanged.connect(self._emit_change)

        self.spn_esp_moldura = QDoubleSpinBox()
        self.spn_esp_moldura.setRange(0.5, 4.0)
        self.spn_esp_moldura.setSingleStep(0.05)
        self.spn_esp_moldura.setValue(1.15)
        self.spn_esp_moldura.valueChanged.connect(self._emit_change)

        self.btn_cor_moldura = ColorButton("#000000", "Cor da Moldura")
        self.btn_cor_moldura.colorChanged.connect(self._emit_change)

        self.spn_intervalo_ticks_y = QDoubleSpinBox()
        self.spn_intervalo_ticks_y.setRange(0.0, 100.0)
        self.spn_intervalo_ticks_y.setSingleStep(1.0)
        self.spn_intervalo_ticks_y.setDecimals(1)
        self.spn_intervalo_ticks_y.setValue(0.0)
        self.spn_intervalo_ticks_y.setSpecialValueText("Automático (Auto)")
        self.spn_intervalo_ticks_y.setToolTip(
            "Espaçamento numérico entre cada traço principal (tick) do eixo Y.\n"
            "'Automático' calcula a divisão ideal (ex: 2, 5, 10) evitando aglomeração de números."
        )
        self.spn_intervalo_ticks_y.valueChanged.connect(self._emit_change)

        form_ticks.addRow("Intervalo Y (Passo):", self.spn_intervalo_ticks_y)
        form_ticks.addRow("Direção:", self.cmb_dir_ticks)
        form_ticks.addRow("Espessura:", self.spn_esp_moldura)
        form_ticks.addRow("Cor:", self.btn_cor_moldura)
        l_gticks.addLayout(form_ticks)
        l_eixos.addWidget(grp_ticks)

        grp_grade = QGroupBox("Linhas de Grade (Grid de Apoio)")
        l_grade = QVBoxLayout(grp_grade)
        l_grade.setSpacing(6)
        self.chk_grade = QCheckBox("Exibir grade de apoio (Linhas — Eixos X e Y)")
        self.chk_grade.setChecked(True)
        self.chk_grade.toggled.connect(self._on_grade_toggled)
        self.chk_grade_barras = QCheckBox("Exibir grade horizontal (Barras)")
        self.chk_grade_barras.toggled.connect(self._emit_change)
        l_grade.addWidget(self.chk_grade)
        l_grade.addWidget(self.chk_grade_barras)
        l_eixos.addWidget(grp_grade)

        l_eixos.addStretch()
        self.tab_estilos.addTab(tab_eixos, get_icon("sliders", size=15), "Eixos")

        # ABA 3: Legenda
        tab_legenda = QWidget()
        l_leg = QVBoxLayout(tab_legenda)
        l_leg.setContentsMargins(6, 8, 6, 8)
        l_leg.setSpacing(10)

        grp_leg = QGroupBox("Configuração da Legenda")
        l_gleg = QVBoxLayout(grp_leg)
        l_gleg.setSpacing(6)

        self.chk_exibir_leg = QCheckBox("Exibir legenda no gráfico")
        self.chk_exibir_leg.setChecked(True)
        self.chk_moldura_leg = QCheckBox("Caixa de contorno na legenda")
        self.chk_moldura_leg.setChecked(True)
        for chk in (self.chk_exibir_leg, self.chk_moldura_leg):
            chk.toggled.connect(self._emit_change)
            l_gleg.addWidget(chk)

        form_leg = QFormLayout()
        form_leg.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_leg.setLabelAlignment(Qt.AlignLeft)
        form_leg.setHorizontalSpacing(8)
        form_leg.setVerticalSpacing(6)

        self.cmb_orient_leg = QComboBox()
        self.cmb_orient_leg.addItems(["Vertical (Empilhados)", "Horizontal (Lado a lado)"])
        self.cmb_orient_leg.currentIndexChanged.connect(self._emit_change)

        self.cmb_pos_preset = QComboBox()
        self.cmb_pos_preset.addItems(POSICOES_LEGENDA)
        self.cmb_pos_preset.currentIndexChanged.connect(self._on_pos_preset_changed)

        self.spn_leg_x = QDoubleSpinBox()
        self.spn_leg_x.setRange(-0.50, 1.50)
        self.spn_leg_x.setSingleStep(0.02)
        self.spn_leg_x.setValue(0.98)
        self.spn_leg_x.valueChanged.connect(self._emit_change)

        self.spn_leg_y = QDoubleSpinBox()
        self.spn_leg_y.setRange(-0.50, 1.50)
        self.spn_leg_y.setSingleStep(0.02)
        self.spn_leg_y.setValue(0.98)
        self.spn_leg_y.valueChanged.connect(self._emit_change)

        form_leg.addRow("Orientação:", self.cmb_orient_leg)
        form_leg.addRow("Posição:", self.cmb_pos_preset)
        form_leg.addRow("Coord. X:", self.spn_leg_x)
        form_leg.addRow("Coord. Y:", self.spn_leg_y)
        l_gleg.addLayout(form_leg)
        l_leg.addWidget(grp_leg)

        l_leg.addStretch()
        self.tab_estilos.addTab(tab_legenda, get_icon("tag", size=15), "Legenda")

        # ABA 4: Cores & Paletas
        tab_cores = QWidget()
        l_cores = QVBoxLayout(tab_cores)
        l_cores.setContentsMargins(6, 8, 6, 8)
        l_cores.setSpacing(10)

        # Paleta Linhas
        self.grp_cores_linhas = QGroupBox("Paleta de Cores — Linhas")
        cl_layout = QVBoxLayout(self.grp_cores_linhas)
        cl_layout.setSpacing(6)

        self.cmb_paleta_linhas = QComboBox()
        self.cmb_paleta_linhas.addItems(list(PALETAS_LINHAS.keys()) + ["Personalizada (Definir manualmente)"])
        self.cmb_paleta_linhas.currentIndexChanged.connect(self._on_paleta_linhas_changed)
        cl_layout.addWidget(self.cmb_paleta_linhas)

        self.widget_cores_linhas_custom = QWidget()
        vl_cl_custom = QVBoxLayout(self.widget_cores_linhas_custom)
        vl_cl_custom.setContentsMargins(0, 4, 0, 0)
        vl_cl_custom.setSpacing(6)
        self.btn_cor_manha = ColorButton("#222222", "Manhã")
        self.btn_cor_tarde = ColorButton("#e74c3c", "Tarde")
        self.btn_cor_noite = ColorButton("#2980b9", "Noite")
        for b in (self.btn_cor_manha, self.btn_cor_tarde, self.btn_cor_noite):
            b.colorChanged.connect(self._emit_change)
            vl_cl_custom.addWidget(b)
        self.widget_cores_linhas_custom.setVisible(False)
        cl_layout.addWidget(self.widget_cores_linhas_custom)
        l_cores.addWidget(self.grp_cores_linhas)

        # Paleta Barras
        self.grp_cores_barras = QGroupBox("Paleta de Cores — Barras")
        cb_layout = QVBoxLayout(self.grp_cores_barras)
        cb_layout.setSpacing(6)

        self.cmb_paleta_barras = QComboBox()
        self.cmb_paleta_barras.addItems(list(PALETAS_BARRAS.keys()) + ["Personalizada (Definir manualmente)"])
        self.cmb_paleta_barras.currentIndexChanged.connect(self._on_paleta_barras_changed)
        cb_layout.addWidget(self.cmb_paleta_barras)

        self.widget_cores_barras_custom = QWidget()
        vl_cb_custom = QVBoxLayout(self.widget_cores_barras_custom)
        vl_cb_custom.setContentsMargins(0, 4, 0, 0)
        vl_cb_custom.setSpacing(6)
        self.btn_cor_bosque = ColorButton("#fdc086", "Bosque")
        self.btn_cor_db = ColorButton("#8fd194", "Desvio Bosque")
        self.btn_cor_estac = ColorButton("#c2b2d6", "Estacionamento")
        self.btn_cor_de = ColorButton("#ffff99", "Desvio Estacionamento")
        for b in (self.btn_cor_bosque, self.btn_cor_db, self.btn_cor_estac, self.btn_cor_de):
            b.colorChanged.connect(self._emit_change)
            vl_cb_custom.addWidget(b)
        self.widget_cores_barras_custom.setVisible(False)
        cb_layout.addWidget(self.widget_cores_barras_custom)
        self.grp_cores_barras.setVisible(False)
        l_cores.addWidget(self.grp_cores_barras)

        l_cores.addStretch()
        self.tab_estilos.addTab(tab_cores, get_icon("palette", size=15), "Cores")

    def configurar_modo(self, tipo_grafico: str):
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        is_linhas = tipo_grafico == "linhas"

        self.rb_linhas.setChecked(is_linhas)
        self.rb_barras.setChecked(not is_linhas)

        self.grp_cores_linhas.setVisible(is_linhas)
        self.grp_opcoes_linhas.setVisible(is_linhas)
        self.chk_grade.setVisible(is_linhas)

        self.grp_cores_barras.setVisible(not is_linhas)
        self.grp_opcoes_barras.setVisible(not is_linhas)
        self.chk_grade_barras.setVisible(not is_linhas)
        self._updating_ui = False

    def carregar_config(self, cfg: dict, tipo_grafico: str = "linhas"):
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        self.configurar_modo(tipo_grafico)
        self._updating_ui = True

        self._set_combo_text(self.cmb_fonte, cfg.get("opcao_fonte", DEFAULT_CONFIG["opcao_fonte"]))
        self.spn_tam_fonte.setValue(float(cfg.get("tamanho_fonte", 11.0)))

        self._set_combo_text(self.cmb_paleta_linhas, cfg.get("opcao_paleta", DEFAULT_CONFIG["opcao_paleta"]))
        self.btn_cor_manha.set_color(cfg.get("cor_manha", "#222222"))
        self.btn_cor_tarde.set_color(cfg.get("cor_tarde", "#e74c3c"))
        self.btn_cor_noite.set_color(cfg.get("cor_noite", "#2980b9"))
        self.widget_cores_linhas_custom.setVisible("Personalizada" in self.cmb_paleta_linhas.currentText())

        self._set_combo_text(
            self.cmb_paleta_barras, cfg.get("opcao_paleta_barras", DEFAULT_CONFIG["opcao_paleta_barras"])
        )
        self.btn_cor_bosque.set_color(cfg.get("cor_bosque", "#fdc086"))
        self.btn_cor_db.set_color(cfg.get("cor_desvio_bosque", "#8fd194"))
        self.btn_cor_estac.set_color(cfg.get("cor_estacionamento", "#c2b2d6"))
        self.btn_cor_de.set_color(cfg.get("cor_desvio_estacionamento", "#ffff99"))
        self.widget_cores_barras_custom.setVisible("Personalizada" in self.cmb_paleta_barras.currentText())

        modo_linhas = cfg.get("modo_estilo_linhas")
        if not modo_linhas:
            if cfg.get("com_marcadores") and not cfg.get("com_linhas_distintas"):
                modo_linhas = "Opção 1: Linha + Símbolo (Line + Symbol)"
            elif cfg.get("com_linhas_distintas") and not cfg.get("com_marcadores"):
                modo_linhas = "Opção 2: Estilos de Traçado (Dash Type)"
            elif cfg.get("com_marcadores") and cfg.get("com_linhas_distintas"):
                modo_linhas = "Personalizado (Avançado)"
            else:
                modo_linhas = "Linhas Contínuas Padrão"

        self._set_combo_text(self.cmb_modo_linhas, modo_linhas)
        self.spn_esp_linha.setValue(float(cfg.get("espessura_linha", 1.2)))
        self.spn_tam_marcador.setValue(float(cfg.get("tamanho_marcador", 6.0)))
        self.chk_descritivo_legenda.setChecked(bool(cfg.get("rotulos_descritivos_legenda", True)))

        self._set_combo_data(self.cmb_traco_manha, cfg.get("traco_manha", "-"))
        self._set_combo_data(self.cmb_traco_tarde, cfg.get("traco_tarde", "-"))
        self._set_combo_data(self.cmb_traco_noite, cfg.get("traco_noite", "-"))

        self._set_combo_data(self.cmb_simbolo_manha, cfg.get("marcador_manha", "o"))
        self._set_combo_data(self.cmb_simbolo_tarde, cfg.get("marcador_tarde", "s"))
        self._set_combo_data(self.cmb_simbolo_noite, cfg.get("marcador_noite", "^"))

        self._atualizar_visibilidade_modo_linhas()

        self.chk_marcadores.setChecked(bool(cfg.get("com_marcadores", True)))
        self.chk_linhas_distintas.setChecked(bool(cfg.get("com_linhas_distintas", False)))
        exibir_gr = bool(cfg.get("exibir_grade", DEFAULT_CONFIG.get("exibir_grade", True)))
        self.chk_grade.setChecked(exibir_gr)
        self.chk_grade_estilo.setChecked(exibir_gr)
        self.chk_grade_barras.setChecked(exibir_gr)

        self.chk_exibir_valores_barras.setChecked(bool(cfg.get("exibir_valores_barras", True)))
        self.chk_negrito_barras.setChecked(bool(cfg.get("negrito_valores_barras", True)))
        self._set_combo_text(
            self.cmb_fmt_decimais, cfg.get("formato_decimais_barras", DEFAULT_CONFIG["formato_decimais_barras"])
        )
        self.spn_largura_grupo.setValue(float(cfg.get("largura_grupo_barras", 0.68)))

        self.chk_exibir_leg.setChecked(bool(cfg.get("exibir_legenda", True)))
        self.chk_moldura_leg.setChecked(bool(cfg.get("moldura_legenda", True)))
        self._set_combo_text(self.cmb_orient_leg, cfg.get("orientacao_leg", "Vertical (Empilhados)"))
        self._set_combo_text(self.cmb_pos_preset, cfg.get("posicao_preset", "Superior Direito (Interno)"))
        self.spn_leg_x.setValue(float(cfg.get("leg_x", 0.98)))
        self.spn_leg_y.setValue(float(cfg.get("leg_y", 0.98)))

        self.chk_b_top.setChecked(bool(cfg.get("borda_top", True)))
        self.chk_b_bot.setChecked(bool(cfg.get("borda_bottom", True)))
        self.chk_b_left.setChecked(bool(cfg.get("borda_left", True)))
        self.chk_b_right.setChecked(bool(cfg.get("borda_right", True)))

        self.chk_t_top.setChecked(bool(cfg.get("ticks_topo", True)))
        self.chk_t_bot.setChecked(bool(cfg.get("ticks_baixo", True)))
        self.chk_t_left.setChecked(bool(cfg.get("ticks_esq", True)))
        self.chk_t_right.setChecked(bool(cfg.get("ticks_dir", True)))
        self._set_combo_text(self.cmb_dir_ticks, cfg.get("direcao_ticks", "Para dentro (in)"))
        self.chk_minor_ticks.setChecked(bool(cfg.get("minor_ticks", True)))
        self.btn_cor_moldura.set_color(cfg.get("cor_moldura", "#000000"))
        self.spn_esp_moldura.setValue(float(cfg.get("esp_moldura", 1.15)))
        self.spn_intervalo_ticks_y.setValue(float(cfg.get("intervalo_ticks_y", 0.0)))

        self._updating_ui = False

    def obter_config(self) -> dict:
        exibir_grade = (
            self.chk_grade.isChecked() if self.tipo_grafico == "linhas" else self.chk_grade_barras.isChecked()
        )
        modo_atual = self.cmb_modo_linhas.currentText()
        return {
            "opcao_fonte": self.cmb_fonte.currentText(),
            "tamanho_fonte": float(self.spn_tam_fonte.value()),
            "opcao_paleta": self.cmb_paleta_linhas.currentText(),
            "cor_manha": self.btn_cor_manha.get_color(),
            "cor_tarde": self.btn_cor_tarde.get_color(),
            "cor_noite": self.btn_cor_noite.get_color(),
            "opcao_paleta_barras": self.cmb_paleta_barras.currentText(),
            "cor_bosque": self.btn_cor_bosque.get_color(),
            "cor_desvio_bosque": self.btn_cor_db.get_color(),
            "cor_estacionamento": self.btn_cor_estac.get_color(),
            "cor_desvio_estacionamento": self.btn_cor_de.get_color(),
            "exibir_valores_barras": self.chk_exibir_valores_barras.isChecked(),
            "formato_decimais_barras": self.cmb_fmt_decimais.currentText(),
            "negrito_valores_barras": self.chk_negrito_barras.isChecked(),
            "largura_grupo_barras": float(self.spn_largura_grupo.value()),
            "espessura_linha": float(self.spn_esp_linha.value()),
            "modo_estilo_linhas": modo_atual,
            "tamanho_marcador": float(self.spn_tam_marcador.value()),
            "rotulos_descritivos_legenda": self.chk_descritivo_legenda.isChecked(),
            "traco_manha": self.cmb_traco_manha.currentData() or "-",
            "traco_tarde": self.cmb_traco_tarde.currentData() or "-",
            "traco_noite": self.cmb_traco_noite.currentData() or "-",
            "marcador_manha": self.cmb_simbolo_manha.currentData() or "o",
            "marcador_tarde": self.cmb_simbolo_tarde.currentData() or "s",
            "marcador_noite": self.cmb_simbolo_noite.currentData() or "^",
            "com_marcadores": "Símbolo" in modo_atual or ("Personalizado" in modo_atual),
            "exibir_grade": exibir_grade,
            "com_linhas_distintas": "Traçado" in modo_atual or ("Personalizado" in modo_atual),
            "exibir_legenda": self.chk_exibir_leg.isChecked(),
            "moldura_legenda": self.chk_moldura_leg.isChecked(),
            "orientacao_leg": self.cmb_orient_leg.currentText(),
            "posicao_preset": self.cmb_pos_preset.currentText(),
            "leg_x": float(self.spn_leg_x.value()),
            "leg_y": float(self.spn_leg_y.value()),
            "borda_top": self.chk_b_top.isChecked(),
            "borda_bottom": self.chk_b_bot.isChecked(),
            "borda_left": self.chk_b_left.isChecked(),
            "borda_right": self.chk_b_right.isChecked(),
            "ticks_topo": self.chk_t_top.isChecked(),
            "ticks_dir": self.chk_t_right.isChecked(),
            "ticks_baixo": self.chk_t_bot.isChecked(),
            "ticks_esq": self.chk_t_left.isChecked(),
            "direcao_ticks": self.cmb_dir_ticks.currentText(),
            "minor_ticks": self.chk_minor_ticks.isChecked(),
            "cor_moldura": self.btn_cor_moldura.get_color(),
            "esp_moldura": float(self.spn_esp_moldura.value()),
            "intervalo_ticks_y": float(self.spn_intervalo_ticks_y.value()),
        }

    def obter_cores_linhas_ativas(self) -> dict:
        paleta = self.cmb_paleta_linhas.currentText()
        if paleta in PALETAS_LINHAS:
            return PALETAS_LINHAS[paleta]
        return {
            "Manha": self.btn_cor_manha.get_color(),
            "Tarde": self.btn_cor_tarde.get_color(),
            "Noite": self.btn_cor_noite.get_color(),
        }

    def obter_cores_barras_ativas(self) -> dict:
        paleta = self.cmb_paleta_barras.currentText()
        if paleta in PALETAS_BARRAS:
            return PALETAS_BARRAS[paleta]
        return {
            "Bosque": self.btn_cor_bosque.get_color(),
            "Desvio_Bosque": self.btn_cor_db.get_color(),
            "Estacionamento": self.btn_cor_estac.get_color(),
            "Desvio_Estacionamento": self.btn_cor_de.get_color(),
        }

    def obter_loc_ancora_legenda(self) -> str:
        preset = self.cmb_pos_preset.currentText()
        if preset in COORDENADAS_LEGENDA_PRESET:
            return COORDENADAS_LEGENDA_PRESET[preset][2]
        return "upper right"

    @staticmethod
    def _set_combo_text(combo: QComboBox, text: str):
        idx = combo.findText(text)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    @staticmethod
    def _set_combo_data(combo: QComboBox, data_val: str):
        for i in range(combo.count()):
            if str(combo.itemData(i)) == str(data_val):
                combo.setCurrentIndex(i)
                return

    def _on_modo_linhas_changed(self):
        self._atualizar_visibilidade_modo_linhas()
        self._emit_change()

    def _atualizar_visibilidade_modo_linhas(self):
        modo = self.cmb_modo_linhas.currentText()
        is_custom = "Personalizado" in modo
        is_simbolo = "Símbolo" in modo or is_custom
        self.spn_tam_marcador.setEnabled(is_simbolo)
        self.lbl_tam_marcador.setEnabled(is_simbolo)
        self.frame_custom_linhas.setVisible(is_custom)

    def _on_grade_estilo_toggled(self, checked: bool):
        if not self._updating_ui:
            self._updating_ui = True
            self.chk_grade.setChecked(checked)
            self._updating_ui = False
            self._emit_change()

    def _on_grade_toggled(self, checked: bool):
        if not self._updating_ui:
            self._updating_ui = True
            self.chk_grade_estilo.setChecked(checked)
            self._updating_ui = False
            self._emit_change()

    def _on_modo_toggled(self):
        if self._updating_ui:
            return
        novo_modo = "linhas" if self.rb_linhas.isChecked() else "barras"
        if novo_modo != self.tipo_grafico:
            self.modeChangeRequested.emit(novo_modo)

    def _on_preset_chosen(self, index: int):
        if self._updating_ui or index <= 0:
            return
        texto = self.cmb_presets.currentText()
        self._updating_ui = True
        self.cmb_presets.setCurrentIndex(0)
        self._updating_ui = False
        self.presetSelected.emit(texto)

    def _on_paleta_linhas_changed(self):
        self.widget_cores_linhas_custom.setVisible("Personalizada" in self.cmb_paleta_linhas.currentText())
        self._emit_change()

    def _on_paleta_barras_changed(self):
        self.widget_cores_barras_custom.setVisible("Personalizada" in self.cmb_paleta_barras.currentText())
        self._emit_change()

    def _on_pos_preset_changed(self):
        if self._updating_ui:
            return
        preset = self.cmb_pos_preset.currentText()
        if preset in COORDENADAS_LEGENDA_PRESET:
            px, py, _ = COORDENADAS_LEGENDA_PRESET[preset]
            self._updating_ui = True
            self.spn_leg_x.setValue(px)
            self.spn_leg_y.setValue(py)
            self._updating_ui = False
        self._emit_change()

    def _emit_change(self):
        if not self._updating_ui:
            self.configChanged.emit()
