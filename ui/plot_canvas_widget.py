"""
Widget de visualização gráfica interativa (Matplotlib FigureCanvasQTAgg + NavigationToolbar)
com suporte a arraste de legenda pelo mouse e exportação em PNG (300 DPI), PDF Vetorial e Excel (.xlsx).
"""

import io
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


class PlotCanvasWidget(QWidget):
    """Área direita da aplicação contendo o gráfico Matplotlib interativo e botões de exportação."""

    seriesVisibilityChanged = Signal()
    exportExcelRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self.tipo_grafico = "linhas"

        self.fig = Figure(figsize=(7.2, 4.5), dpi=125)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Título da seção
        lbl_titulo = QLabel("<b>Visualização Gráfica Interativa (Padrão OriginLab Pro)</b>")
        lbl_titulo.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl_titulo)

        # Barra de séries visíveis
        self.frame_series = QFrame()
        self.frame_series.setFrameShape(QFrame.StyledPanel)
        series_layout = QHBoxLayout(self.frame_series)
        series_layout.setContentsMargins(10, 6, 10, 6)

        lbl_vis = QLabel("<b>Séries visíveis:</b>")
        series_layout.addWidget(lbl_vis)

        # Checkboxes modo linhas
        self.chk_manha = QCheckBox("Manhã")
        self.chk_tarde = QCheckBox("Tarde")
        self.chk_noite = QCheckBox("Noite")
        for chk in (self.chk_manha, self.chk_tarde, self.chk_noite):
            chk.setChecked(True)
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
            chk.toggled.connect(self._on_series_toggled)
            series_layout.addWidget(chk)

        series_layout.addStretch()
        layout.addWidget(self.frame_series)

        # Dica de interatividade da legenda
        lbl_dica = QLabel(
            "💡 <i>Dica: Clique e arraste a <b>legenda</b> diretamente com o mouse sobre o gráfico "
            "para posicioná-la livremente, ou use a barra abaixo para dar zoom/pan.</i>"
        )
        lbl_dica.setWordWrap(True)
        lbl_dica.setStyleSheet("color: #555555; font-size: 11.5px; padding: 2px 4px;")
        layout.addWidget(lbl_dica)

        # Barra de navegação nativa do Matplotlib
        layout.addWidget(self.toolbar)

        # Canvas principal do gráfico
        self.canvas.setMinimumSize(480, 360)
        layout.addWidget(self.canvas, stretch=1)

        # Barra inferior de Exportação Rápida
        frame_exp = QFrame()
        frame_exp.setFrameShape(QFrame.StyledPanel)
        exp_layout = QHBoxLayout(frame_exp)
        exp_layout.setContentsMargins(10, 8, 10, 8)
        exp_layout.setSpacing(10)

        self.btn_png = QPushButton("🖼️ Exportar PNG (300 DPI)")
        self.btn_png.setCursor(Qt.PointingHandCursor)
        self.btn_png.setMinimumHeight(34)
        self.btn_png.clicked.connect(self._exportar_png)

        self.btn_pdf = QPushButton("📄 Exportar Vetor PDF (Publicação)")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setMinimumHeight(34)
        self.btn_pdf.clicked.connect(self._exportar_pdf)

        self.btn_excel = QPushButton("📊 Exportar Planilha Excel (.xlsx)")
        self.btn_excel.setCursor(Qt.PointingHandCursor)
        self.btn_excel.setMinimumHeight(34)
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
                QMessageBox.information(self, "Exportação Concluída", f"Imagem PNG (300 DPI) salva em:\n{caminho}")
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
                QMessageBox.information(self, "Exportação Concluída", f"Arquivo PDF vetorial salvo em:\n{caminho}")
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
