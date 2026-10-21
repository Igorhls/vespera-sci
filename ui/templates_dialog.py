"""
Diálogo de Galeria de Modelos Prontos (Templates) para o Vespera Sci Desktop.
Apresenta cartões visuais para seleção rápida de modelos acadêmicos e presets experimentais.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.presets import (
    PRESETS_BARRAS,
    PRESETS_BOXPLOT,
    PRESETS_DISPERSAO,
    PRESETS_LINHAS,
)
from ui.icons import get_icon


class TemplatesGalleryDialog(QDialog):
    """Galeria visual de modelos pré-configurados para início rápido de projetos."""

    templateSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Galeria de Modelos Científicos e Presets")
        self.resize(780, 520)
        self.setMinimumSize(640, 420)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(4)
        lbl_tit = QLabel("<b>Galeria de Modelos Prontos e Presets Experimentais</b>")
        lbl_tit.setStyleSheet("font-size: 16px;")
        lbl_sub = QLabel(
            "Selecione um modelo abaixo para inicializar seu projeto com dados reais de pesquisa, "
            "configurações estéticas pré-calibradas e formatação acadêmica."
        )
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("color: #64748b; font-size: 12px;")
        header.addWidget(lbl_tit)
        header.addWidget(lbl_sub)
        root.addLayout(header)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        # Aba 1: Linhas e Séries Temporais
        self.tabs.addTab(
            self._criar_aba_modelos(
                PRESETS_LINHAS,
                "Monitoramento espaço-temporal contínuo (Pontos P1 a Pn) com marcadores geométricos.",
            ),
            get_icon("chart-line", size=15),
            "Séries Temporais (Linhas)",
        )

        # Aba 2: Barras e Desvio Padrão
        self.tabs.addTab(
            self._criar_aba_modelos(
                PRESETS_BARRAS,
                "Comparativos de médias e dispersão amostral com hachuras OriginLab e rótulos numéricos.",
            ),
            get_icon("chart-bar", size=15),
            "Barras Agrupadas & Desvio",
        )

        # Aba 3: Dispersão e Regressão Linear
        self.tabs.addTab(
            self._criar_aba_modelos(
                PRESETS_DISPERSAO,
                "Análise bivariada (X vs Y), reta de regressão linear, correlação de Pearson e cálculo de R².",
            ),
            get_icon("chart-scatter", size=15),
            "Dispersão & Regressão R²",
        )

        # Aba 4: Boxplot e Distribuição
        self.tabs.addTab(
            self._criar_aba_modelos(
                PRESETS_BOXPLOT,
                "Diagramas de caixas com quartis Q1/Q3, mediana, whiskers (1,5×IQR) e detecção de outliers.",
            ),
            get_icon("sliders", size=15),
            "Boxplot & Distribuição",
        )

        # Rodapé
        footer = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        footer.addStretch()
        footer.addWidget(btn_cancelar)
        root.addLayout(footer)

    def _criar_aba_modelos(self, presets_dict: dict, descricao_aba: str) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        lbl_desc = QLabel(f"<span style='color: #64748b; font-size: 11.5px;'>{descricao_aba}</span>")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        for nome, dados in presets_dict.items():
            card = QFrame()
            card.setObjectName("cardPanel")
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(12, 10, 12, 10)
            c_layout.setSpacing(12)

            info = QVBoxLayout()
            info.setSpacing(3)
            lbl_nome = QLabel(f"<b>{nome}</b>")
            lbl_nome.setStyleSheet("font-size: 13px;")

            desc_extra = dados.get("titulo_grafico") or dados.get("rotulo_y") or ""
            qtd_pontos = len(dados.get("df", []))
            lbl_sub = QLabel(
                f"<span style='color: #64748b; font-size: 11px;'>{desc_extra} • {qtd_pontos} observações cadastradas</span>"
            )
            info.addWidget(lbl_nome)
            info.addWidget(lbl_sub)
            c_layout.addLayout(info, stretch=1)

            btn_usar = QPushButton("Carregar Modelo")
            btn_usar.setIcon(get_icon("check", color="#ffffff", size=14))
            btn_usar.setObjectName("btnPrimary")
            btn_usar.setCursor(Qt.PointingHandCursor)
            btn_usar.clicked.connect(lambda _, n=nome: self._selecionar(n))
            c_layout.addWidget(btn_usar)

            layout.addWidget(card)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _selecionar(self, nome_preset: str):
        self.templateSelected.emit(nome_preset)
        self.accept()
