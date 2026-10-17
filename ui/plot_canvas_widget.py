"""
Widget de visualização gráfica interativa (Matplotlib FigureCanvasQTAgg + NavigationToolbar).
Repaginação visual completa: ícones vetoriais SVG, sem emojis e botões de exportação destacados.
"""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.icons import get_icon


class PlotCanvasWidget(QWidget):
    """Área direita da aplicação contendo o gráfico Matplotlib interativo e botões de exportação."""

    seriesVisibilityChanged = Signal()
    exportExcelRequested = Signal(str)
    hideRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self.tipo_grafico = "linhas"

        self.fig = Figure(figsize=(8.5, 5.3), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # 1. Barra Superior Integrada: Séries no Gráfico + Dica de Interatividade
        self.frame_series = QFrame()
        self.frame_series.setObjectName("cardPanel")
        series_layout = QHBoxLayout(self.frame_series)
        series_layout.setContentsMargins(12, 8, 12, 8)
        series_layout.setSpacing(10)

        lbl_vis = QLabel("<b>Séries no Gráfico:</b>")
        series_layout.addWidget(lbl_vis)

        # Checkboxes modo linhas
        self.chk_manha = QCheckBox("Manhã")
        self.chk_tarde = QCheckBox("Tarde")
        self.chk_noite = QCheckBox("Noite")
        for chk in (self.chk_manha, self.chk_tarde, self.chk_noite):
            chk.setChecked(True)
            chk.setCursor(Qt.PointingHandCursor)
            chk.toggled.connect(self._on_series_toggled)
            series_layout.addWidget(chk)

        # Checkboxes modo barras
        self.chk_bosque = QCheckBox("Bosque")
        self.chk_desvio_bosque = QCheckBox("Desvio/p (1)")
        self.chk_estac = QCheckBox("Estacionamento")
        self.chk_desvio_estac = QCheckBox("Desvio/p (2)")
        for chk in (self.chk_bosque, self.chk_desvio_bosque, self.chk_estac, self.chk_desvio_estac):
            chk.setChecked(True)
            chk.setVisible(False)
            chk.setCursor(Qt.PointingHandCursor)
            chk.toggled.connect(self._on_series_toggled)
            series_layout.addWidget(chk)

        series_layout.addStretch()

        lbl_dica = QLabel(
            "<span style='color: #64748b; font-size: 11px;'><b>Dica:</b> Arraste a legenda livremente &bull; Barra inferior para zoom e pan</span>"
        )
        series_layout.addWidget(lbl_dica)

        self.btn_hide = QPushButton(" Ocultar")
        self.btn_hide.setIcon(get_icon("x", size=13))
        self.btn_hide.setToolTip("Ocultar Área do Gráfico (Ctrl+G)")
        self.btn_hide.setCursor(Qt.PointingHandCursor)
        self.btn_hide.clicked.connect(self.hideRequested.emit)
        series_layout.addWidget(self.btn_hide)

        layout.addWidget(self.frame_series)

        # 2. Canvas Principal em Card Moderno
        canvas_card = QFrame()
        canvas_card.setObjectName("cardPanel")
        cc_layout = QVBoxLayout(canvas_card)
        cc_layout.setContentsMargins(6, 6, 6, 6)
        cc_layout.setSpacing(6)
        cc_layout.setAlignment(Qt.AlignCenter)

        self.canvas.setFixedSize(850, 530)
        cc_layout.addWidget(self.canvas, 0, Qt.AlignCenter)
        cc_layout.addWidget(self.toolbar, 0, Qt.AlignCenter)

        layout.addWidget(canvas_card, stretch=1)

        # 4. Barra Inferior de Exportação com Ícones Vetoriais
        frame_exp = QFrame()
        frame_exp.setObjectName("cardPanel")
        exp_layout = QHBoxLayout(frame_exp)
        exp_layout.setContentsMargins(12, 10, 12, 10)
        exp_layout.setSpacing(10)

        self.btn_png = QPushButton("Exportar PNG (300 DPI)")
        self.btn_png.setIcon(get_icon("file-image", color="#ffffff", size=16))
        self.btn_png.setObjectName("btnPrimary")
        self.btn_png.setCursor(Qt.PointingHandCursor)
        self.btn_png.setMinimumHeight(36)
        self.btn_png.clicked.connect(self._exportar_png)

        self.btn_pdf = QPushButton("Vetor PDF (Publicação)")
        self.btn_pdf.setIcon(get_icon("file-pdf", color="#ffffff", size=16))
        self.btn_pdf.setObjectName("btnSuccess")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setMinimumHeight(36)
        self.btn_pdf.clicked.connect(self._exportar_pdf)

        self.btn_excel = QPushButton("Planilha Excel (.xlsx)")
        self.btn_excel.setIcon(get_icon("file-spreadsheet", size=16))
        self.btn_excel.setCursor(Qt.PointingHandCursor)
        self.btn_excel.setMinimumHeight(36)
        self.btn_excel.clicked.connect(self._solicitar_exportacao_excel)

        exp_layout.addWidget(self.btn_png)
        exp_layout.addWidget(self.btn_pdf)
        exp_layout.addWidget(self.btn_excel)

        layout.addWidget(frame_exp)

        self._nome_base_padrao = "grafico"

    def definir_nome_base_exportacao(self, nome: str):
        limpo = (nome or "grafico").strip().replace(" ", "_").lower()
        self._nome_base_padrao = limpo or "grafico"

    def configurar_modo(self, tipo_grafico: str, rotulos_barras: dict = None):
        """Alterna os checkboxes visíveis conforme o modo ('linhas' ou 'barras')."""
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        is_linhas = tipo_grafico == "linhas"

        for chk in (self.chk_manha, self.chk_tarde, self.chk_noite):
            chk.setVisible(is_linhas)

        for chk in (self.chk_bosque, self.chk_desvio_bosque, self.chk_estac, self.chk_desvio_estac):
            chk.setVisible(not is_linhas)

        if rotulos_barras:
            self.chk_bosque.setText(rotulos_barras.get("Bosque", "Bosque"))
            self.chk_desvio_bosque.setText(f"{rotulos_barras.get('Desvio_Bosque', 'Desvio/p')} (1)")
            self.chk_estac.setText(rotulos_barras.get("Estacionamento", "Estacionamento"))
            self.chk_desvio_estac.setText(f"{rotulos_barras.get('Desvio_Estacionamento', 'Desvio/p')} (2)")

        self._updating_ui = False

    def carregar_estado_series(self, cfg: dict):
        self._updating_ui = True
        self.chk_manha.setChecked(bool(cfg.get("show_manha", True)))
        self.chk_tarde.setChecked(bool(cfg.get("show_tarde", True)))
        self.chk_noite.setChecked(bool(cfg.get("show_noite", True)))
        self.chk_bosque.setChecked(bool(cfg.get("show_bosque", True)))
        self.chk_desvio_bosque.setChecked(bool(cfg.get("show_desvio_bosque", True)))
        self.chk_estac.setChecked(bool(cfg.get("show_estacionamento", True)))
        self.chk_desvio_estac.setChecked(bool(cfg.get("show_desvio_estacionamento", True)))
        self._updating_ui = False

    def obter_estado_series(self) -> dict:
        return {
            "show_manha": self.chk_manha.isChecked(),
            "show_tarde": self.chk_tarde.isChecked(),
            "show_noite": self.chk_noite.isChecked(),
            "show_bosque": self.chk_bosque.isChecked(),
            "show_desvio_bosque": self.chk_desvio_bosque.isChecked(),
            "show_estacionamento": self.chk_estac.isChecked(),
            "show_desvio_estacionamento": self.chk_desvio_estac.isChecked(),
        }

    def obter_series_linhas_ativas(self) -> list:
        ativas = []
        if self.chk_manha.isChecked():
            ativas.append("Manha")
        if self.chk_tarde.isChecked():
            ativas.append("Tarde")
        if self.chk_noite.isChecked():
            ativas.append("Noite")
        return ativas

    def obter_series_barras_ativas(self) -> list:
        ativas = []
        if self.chk_bosque.isChecked():
            ativas.append("Bosque")
        if self.chk_desvio_bosque.isChecked():
            ativas.append("Desvio_Bosque")
        if self.chk_estac.isChecked():
            ativas.append("Estacionamento")
        if self.chk_desvio_estac.isChecked():
            ativas.append("Desvio_Estacionamento")
        return ativas

    def atualizar_canvas(self):
        self.canvas.draw_idle()

    def _on_series_toggled(self):
        if not self._updating_ui:
            self.seriesVisibilityChanged.emit()

    def _exportar_png(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Imagem PNG (300 DPI)",
            f"{self._nome_base_padrao}_figura.png",
            "Imagem PNG (*.png)",
        )
        if caminho:
            try:
                self.fig.savefig(caminho, format="png", dpi=300, bbox_inches="tight")
                QMessageBox.information(self, "Exportação Concluída", f"Imagem PNG (300 DPI) salva com sucesso em:\n{caminho}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Exportar PNG", str(e))

    def _exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Figura Vetorial PDF",
            f"{self._nome_base_padrao}_figura.pdf",
            "Documento PDF (*.pdf)",
        )
        if caminho:
            try:
                self.fig.savefig(caminho, format="pdf", bbox_inches="tight")
                QMessageBox.information(self, "Exportação Concluída", f"Arquivo PDF vetorial salvo com sucesso em:\n{caminho}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Exportar PDF", str(e))

    def _solicitar_exportacao_excel(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Planilha Excel (.xlsx)",
            f"{self._nome_base_padrao}_dados.xlsx",
            "Planilha Excel (*.xlsx)",
        )
        if caminho:
            self.exportExcelRequested.emit(caminho)
