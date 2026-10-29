"""
Widget de visualização gráfica interativa (Matplotlib FigureCanvasQTAgg + NavigationToolbar).
Repaginação visual completa: ícones vetoriais SVG, sem emojis e botões de exportação destacados.
"""

import logging

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
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.icons import get_icon

logger = logging.getLogger(__name__)

# Tamanho físico da figura (polegadas). É o tamanho exportado em PNG/TIFF/PDF/SVG,
# independentemente do tamanho da janela.
LARGURA_FIGURA_POL = 8.5
ALTURA_FIGURA_POL = 5.3


class CanvasProporcional(FigureCanvasQTAgg):
    """
    Canvas cujo tamanho em polegadas é sempre LARGURA x ALTURA_FIGURA_POL.
    Ao redimensionar, só o DPI de tela muda: a prévia funciona como um zoom
    da figura exportada (mesmas proporções de texto, legenda e margens).
    """

    def resizeEvent(self, event):
        if self.figure is not None and event.size().width() > 0:
            try:
                razao = self.device_pixel_ratio or 1.0
                dpi = max(20.0, event.size().width() * razao / LARGURA_FIGURA_POL)
                self.figure._original_dpi = dpi / razao
                self.figure._set_dpi(dpi, forward=False)
            except AttributeError:
                logger.debug("API de DPI do Matplotlib indisponível; usando redimensionamento padrão")
        super().resizeEvent(event)
        # O arredondamento em pixels inteiros alteraria a altura em ~0,01 pol; fixa o tamanho exportado
        if self.figure is not None:
            self.figure.set_size_inches(LARGURA_FIGURA_POL, ALTURA_FIGURA_POL, forward=False)


class MolduraProporcional(QWidget):
    """Mantém o canvas centralizado com a proporção da figura, ocupando o maior espaço possível."""

    def __init__(self, canvas, proporcao: float, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.proporcao = proporcao
        canvas.setParent(self)
        self.setMinimumSize(320, int(320 / proporcao))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        largura = self.width()
        altura = int(largura / self.proporcao)
        if altura > self.height():
            altura = self.height()
            largura = int(altura * self.proporcao)
        self.canvas.setGeometry((self.width() - largura) // 2, (self.height() - altura) // 2, largura, altura)


class PlotCanvasWidget(QWidget):
    """Área direita da aplicação contendo o gráfico Matplotlib interativo e botões de exportação."""

    seriesVisibilityChanged = Signal()
    exportExcelRequested = Signal(str)
    hideRequested = Signal()
    configRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self.tipo_grafico = "linhas"

        self.fig = Figure(figsize=(LARGURA_FIGURA_POL, ALTURA_FIGURA_POL), dpi=100)
        self.canvas = CanvasProporcional(self.fig)
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
        self.series_layout = series_layout
        self.dynamic_chk_series = {}
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

        # Checkboxes modo dispersão
        self.chk_box_bosque = QCheckBox("Bosque")
        self.chk_box_estac = QCheckBox("Estacionamento")
        for chk in (self.chk_box_bosque, self.chk_box_estac):
            chk.setChecked(True)
            chk.setVisible(False)
            chk.setCursor(Qt.PointingHandCursor)
            chk.toggled.connect(self._on_series_toggled)
            series_layout.addWidget(chk)

        self.chk_pontos_disp = QCheckBox("Pontos (X, Y)")
        self.chk_reta_disp = QCheckBox("Linha de Regressão")
        self.chk_r2_disp = QCheckBox("R² no Gráfico")
        for chk in (self.chk_pontos_disp, self.chk_reta_disp, self.chk_r2_disp):
            chk.setChecked(True)
            chk.setVisible(False)
            chk.setCursor(Qt.PointingHandCursor)
            chk.toggled.connect(self._on_series_toggled)
            series_layout.addWidget(chk)

        series_layout.addStretch()

        lbl_dica = QLabel(
            "<span style='color: #64748b; font-size: 11px;'><b>Dica:</b> Arraste a legenda livremente &bull; Barra inferior para zoom e pan</span>"
        )
        # A dica pode encolher (ou sumir) para não forçar a largura mínima do painel
        lbl_dica.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lbl_dica.setMinimumWidth(0)
        series_layout.addWidget(lbl_dica, stretch=1)

        # Configurações ficam na barra superior (ícone de controles / Ctrl+E)
        self.btn_hide = QPushButton()
        self.btn_hide.setObjectName("btnIcon")
        self.btn_hide.setIcon(get_icon("x", size=15))
        self.btn_hide.setToolTip("Ocultar o gráfico (Ctrl+G)")
        self.btn_hide.setAccessibleName("Ocultar o gráfico")
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

        self.moldura_canvas = MolduraProporcional(self.canvas, LARGURA_FIGURA_POL / ALTURA_FIGURA_POL)
        cc_layout.addWidget(self.moldura_canvas, stretch=1)
        cc_layout.addWidget(self.toolbar, 0, Qt.AlignCenter)

        layout.addWidget(canvas_card, stretch=1)

        # 4. Barra Inferior de Exportação com Ícones Vetoriais
        frame_exp = QFrame()
        frame_exp.setObjectName("cardPanel")
        exp_layout = QHBoxLayout(frame_exp)
        exp_layout.setContentsMargins(12, 10, 12, 10)
        exp_layout.setSpacing(10)

        self.btn_png = QPushButton("Exportar Imagem (PNG/TIFF)")
        self.btn_png.setToolTip("PNG a 300 DPI ou TIFF a 600 DPI (exigido por vários periódicos)")
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

        self.btn_svg = QPushButton("Vetor SVG")
        self.btn_svg.setIcon(get_icon("download", size=16))
        self.btn_svg.setCursor(Qt.PointingHandCursor)
        self.btn_svg.setMinimumHeight(36)
        self.btn_svg.clicked.connect(self._exportar_svg)

        self.btn_excel = QPushButton("Planilha Excel (.xlsx)")
        self.btn_excel.setIcon(get_icon("file-spreadsheet", size=16))
        self.btn_excel.setCursor(Qt.PointingHandCursor)
        self.btn_excel.setMinimumHeight(36)
        self.btn_excel.clicked.connect(self._solicitar_exportacao_excel)

        exp_layout.addWidget(self.btn_png)
        exp_layout.addWidget(self.btn_pdf)
        exp_layout.addWidget(self.btn_svg)
        exp_layout.addWidget(self.btn_excel)

        layout.addWidget(frame_exp)

        self._nome_base_padrao = "grafico"

    def definir_nome_base_exportacao(self, nome: str):
        limpo = (nome or "grafico").strip().replace(" ", "_").lower()
        self._nome_base_padrao = limpo or "grafico"

    def atualizar_series_dinamicas(self, colunas_series: list):
        """Atualiza dinamicamente os checkboxes de séries no topo para qualquer quantidade de colunas."""
        self._updating_ui = True
        is_padrao = (set(colunas_series) == {"Manha", "Tarde", "Noite"})
        is_linhas = (self.tipo_grafico == "linhas")

        for chk in (self.chk_manha, self.chk_tarde, self.chk_noite):
            chk.setVisible(is_padrao and is_linhas)

        for col, chk in list(self.dynamic_chk_series.items()):
            if is_padrao or not is_linhas or col not in colunas_series:
                chk.setVisible(False)

        if not is_padrao and is_linhas:
            for idx, col in enumerate(colunas_series):
                if col not in self.dynamic_chk_series:
                    chk = QCheckBox(col)
                    chk.setChecked(True)
                    chk.setCursor(Qt.PointingHandCursor)
                    chk.toggled.connect(self._on_series_toggled)
                    self.series_layout.insertWidget(1 + idx, chk)
                    self.dynamic_chk_series[col] = chk
                else:
                    chk = self.dynamic_chk_series[col]
                    chk.setText(col)
                    chk.setVisible(True)

        self._updating_ui = False

    def configurar_modo(self, tipo_grafico: str, rotulos_barras: dict = None):
        """Alterna os checkboxes visíveis conforme o modo ('linhas', 'barras' ou 'dispersao')."""
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        is_linhas = tipo_grafico == "linhas"
        is_barras = tipo_grafico == "barras"
        is_dispersao = tipo_grafico == "dispersao"
        is_boxplot = tipo_grafico == "boxplot"

        for chk in (self.chk_box_bosque, self.chk_box_estac):
            chk.setVisible(is_boxplot)

        for chk in (self.chk_manha, self.chk_tarde, self.chk_noite):
            chk.setVisible(is_linhas)

        for chk in (self.chk_bosque, self.chk_desvio_bosque, self.chk_estac, self.chk_desvio_estac):
            chk.setVisible(is_barras)

        for chk in (self.chk_pontos_disp, self.chk_reta_disp, self.chk_r2_disp):
            chk.setVisible(is_dispersao)

        if not is_linhas and hasattr(self, "dynamic_chk_series"):
            for chk in self.dynamic_chk_series.values():
                chk.setVisible(False)

        if rotulos_barras and is_barras:
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
        self.chk_pontos_disp.setChecked(bool(cfg.get("show_pontos_dispersao", True)))
        self.chk_reta_disp.setChecked(bool(cfg.get("show_reta_dispersao", True)))
        self.chk_r2_disp.setChecked(bool(cfg.get("show_r2_dispersao", True)))
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
            "show_pontos_dispersao": self.chk_pontos_disp.isChecked(),
            "show_reta_dispersao": self.chk_reta_disp.isChecked(),
            "show_r2_dispersao": self.chk_r2_disp.isChecked(),
        }

    def obter_series_linhas_ativas(self) -> list:
        if self.tipo_grafico != "linhas":
            return []
        if self.chk_manha.isVisible():
            ativas = []
            if self.chk_manha.isChecked():
                ativas.append("Manha")
            if self.chk_tarde.isChecked():
                ativas.append("Tarde")
            if self.chk_noite.isChecked():
                ativas.append("Noite")
            return ativas

        if hasattr(self, "dynamic_chk_series"):
            ativas = [col for col, chk in self.dynamic_chk_series.items() if chk.isVisible() and chk.isChecked()]
            return ativas
        return []

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

    def obter_series_boxplot_ativas(self) -> list:
        ativas = []
        if self.chk_box_bosque.isChecked():
            ativas.append("Bosque")
        if self.chk_box_estac.isChecked():
            ativas.append("Estacionamento")
        return ativas

    def obter_series_dispersao_ativas(self) -> dict:
        return {
            "pontos": self.chk_pontos_disp.isChecked(),
            "reta": self.chk_reta_disp.isChecked(),
            "r2": self.chk_r2_disp.isChecked(),
        }

    def atualizar_canvas(self):
        self.canvas.draw_idle()

    def _on_series_toggled(self):
        if not self._updating_ui:
            self.seriesVisibilityChanged.emit()

    def _exportar_png(self):
        filtro_png = "Imagem PNG 300 DPI (*.png)"
        filtro_tiff = "Imagem TIFF 600 DPI (*.tif *.tiff)"
        caminho, filtro = QFileDialog.getSaveFileName(
            self,
            "Salvar Imagem Rasterizada",
            f"{self._nome_base_padrao}_figura.png",
            f"{filtro_png};;{filtro_tiff}",
        )
        if not caminho:
            return
        e_tiff = caminho.lower().endswith((".tif", ".tiff")) or (
            filtro == filtro_tiff and not caminho.lower().endswith(".png")
        )
        if e_tiff and not caminho.lower().endswith((".tif", ".tiff")):
            caminho += ".tif"
        try:
            if e_tiff:
                self.fig.savefig(
                    caminho, format="tiff", dpi=600, bbox_inches="tight",
                    pil_kwargs={"compression": "tiff_lzw"},
                )
                descricao = "TIFF (600 DPI)"
            else:
                self.fig.savefig(caminho, format="png", dpi=300, bbox_inches="tight")
                descricao = "PNG (300 DPI)"
            QMessageBox.information(self, "Exportação Concluída", f"Imagem {descricao} salva com sucesso em:\n{caminho}")
        except Exception as e:
            logger.exception("Erro ao exportar imagem")
            QMessageBox.critical(self, "Erro ao Exportar Imagem", str(e))

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
                logger.exception("Erro ao exportar PDF")
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

    def _exportar_svg(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Figura Vetorial SVG",
            f"{self._nome_base_padrao}_figura.svg",
            "Vetor SVG (*.svg)",
        )
        if caminho:
            try:
                self.fig.savefig(caminho, format="svg", bbox_inches="tight")
                QMessageBox.information(self, "Exportação Concluída", f"Arquivo vetorial SVG salvo com sucesso em:\n{caminho}")
            except Exception as e:
                logger.exception("Erro ao exportar SVG")
                QMessageBox.critical(self, "Erro ao Exportar SVG", str(e))
