"""
Design System e Folhas de Estilos QSS para o Vespera Sci Desktop.
Suporte completo a Tema Claro (Light Studio) e Tema Escuro (Dark Studio).
"""

THEME_LIGHT = {
    "name": "light",
    "bg_window": "#f8fafc",
    "bg_card": "#ffffff",
    "bg_card_alt": "#f1f5f9",
    "bg_input": "#ffffff",
    "bg_hover": "#e2e8f0",
    "border": "#cbd5e1",
    "border_subtle": "#e2e8f0",
    "border_focus": "#3b82f6",
    "text_primary": "#0f172a",
    "text_secondary": "#64748b",
    "text_muted": "#94a3b8",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "accent_text": "#ffffff",
    "success": "#16a34a",
    "success_hover": "#15803d",
    "warning": "#f59e0b",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "table_alt_row": "#f8fafc",
    "table_selection": "#dbeafe",
    "table_selection_text": "#1e3a8a",
    "tab_active_bg": "#ffffff",
    "tab_inactive_bg": "#e2e8f0",
    "tab_active_text": "#2563eb",
    "tab_inactive_text": "#64748b",
}

THEME_DARK = {
    "name": "dark",
    "bg_window": "#0f172a",
    "bg_card": "#1e293b",
    "bg_card_alt": "#334155",
    "bg_input": "#0f172a",
    "bg_hover": "#334155",
    "border": "#334155",
    "border_subtle": "#1e293b",
    "border_focus": "#60a5fa",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "accent_text": "#ffffff",
    "success": "#22c55e",
    "success_hover": "#16a34a",
    "warning": "#fbbf24",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "table_alt_row": "#162032",
    "table_selection": "#1e3a8a",
    "table_selection_text": "#eff6ff",
    "tab_active_bg": "#1e293b",
    "tab_inactive_bg": "#0f172a",
    "tab_active_text": "#60a5fa",
    "tab_inactive_text": "#94a3b8",
}


def build_qss(theme: dict) -> str:
    """Gera a folha de estilos QSS com base no dicionário do tema."""
    return f"""
    * {{
        font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", "Helvetica Neue", sans-serif;
        font-size: 12.5px;
        color: {theme['text_primary']};
    }}

    QMainWindow, QWidget#centralWidget {{
        background-color: {theme['bg_window']};
    }}

    QMenuBar {{
        background-color: {theme['bg_card']};
        color: {theme['text_primary']};
        border-bottom: 1px solid {theme['border_subtle']};
        padding: 2px 6px;
    }}
    QMenuBar::item {{
        background: transparent;
        padding: 5px 10px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {theme['bg_hover']};
    }}

    QMenu {{
        background-color: {theme['bg_card']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {theme['accent']};
        color: {theme['accent_text']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {theme['border_subtle']};
        margin: 4px 6px;
    }}

    /* Painéis e Cards */
    QFrame#cardPanel, QFrame#projBar, QFrame#headerBar {{
        background-color: {theme['bg_card']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    /* Grupos com título elegante */
    QGroupBox {{
        font-weight: 700;
        font-size: 12px;
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        margin-top: 24px;
        padding: 14px 10px 10px 10px;
        background-color: {theme['bg_card']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        top: 3px;
        padding: 3px 8px;
        border-radius: 4px;
        background-color: {theme['bg_card_alt']};
        border: 1px solid {theme['border_subtle']};
        color: {theme['accent']};
    }}

    /* Abas Modernas (QTabWidget) */
    QTabWidget::pane {{
        border: 1px solid {theme['border']};
        border-radius: 0 8px 8px 8px;
        background-color: {theme['bg_card']};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {theme['tab_inactive_bg']};
        color: {theme['tab_inactive_text']};
        font-weight: 600;
        font-size: 11.5px;
        padding: 6px 11px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: 1px solid {theme['border']};
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background-color: {theme['tab_active_bg']};
        color: {theme['tab_active_text']};
        border-bottom: 2px solid {theme['accent']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {theme['bg_hover']};
    }}

    /* Botões */
    QPushButton {{
        background-color: {theme['bg_card']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {theme['bg_hover']};
        border-color: {theme['border_focus']};
    }}
    QPushButton:pressed {{
        background-color: {theme['border']};
    }}

    QPushButton#btnPrimary {{
        background-color: {theme['accent']};
        color: {theme['accent_text']};
        border: 1px solid {theme['accent']};
        font-weight: 600;
    }}
    QPushButton#btnPrimary:hover {{
        background-color: {theme['accent_hover']};
        border-color: {theme['accent_hover']};
    }}

    QPushButton#btnSuccess {{
        background-color: {theme['success']};
        color: #ffffff;
        border: 1px solid {theme['success']};
        font-weight: 600;
    }}
    QPushButton#btnSuccess:hover {{
        background-color: {theme['success_hover']};
        border-color: {theme['success_hover']};
    }}

    QPushButton#btnDanger {{
        background-color: transparent;
        color: {theme['danger']};
        border: 1px solid {theme['danger']};
    }}
    QPushButton#btnDanger:hover {{
        background-color: {theme['danger']};
        color: #ffffff;
    }}

    QPushButton#btnSegment {{
        background-color: {theme['bg_card_alt']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
    }}
    QPushButton#btnSegmentActive {{
        background-color: {theme['accent']};
        color: {theme['accent_text']};
        border: 1px solid {theme['accent']};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 700;
    }}

    /* Inputs e Controles */
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPlainTextEdit {{
        background-color: {theme['bg_input']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 6px 8px;
        selection-background-color: {theme['accent']};
        selection-color: {theme['accent_text']};
    }}
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{
        border: 1px solid {theme['border_focus']};
        background-color: {theme['bg_card']};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 22px;
        border-left: 1px solid {theme['border_subtle']};
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {theme['bg_card']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {theme['accent']};
        selection-color: {theme['accent_text']};
    }}

    /* Tabela de Dados */
    QTableWidget, QTableView {{
        background-color: {theme['bg_card']};
        gridline-color: {theme['border_subtle']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        selection-background-color: {theme['table_selection']};
        selection-color: {theme['table_selection_text']};
    }}
    QTableWidget::item {{
        padding: 4px 6px;
    }}
    QTableWidget::item:alternate {{
        background-color: {theme['table_alt_row']};
    }}
    QHeaderView {{
        background-color: {theme['bg_card_alt']};
    }}
    QHeaderView::section {{
        background-color: {theme['bg_card_alt']};
        color: {theme['text_secondary']};
        font-weight: 700;
        font-size: 11.5px;
        padding: 6px 8px;
        border: none;
        border-right: 1px solid {theme['border_subtle']};
        border-bottom: 1px solid {theme['border']};
    }}
    QTableCornerButton::section {{
        background-color: {theme['bg_card_alt']};
        border: none;
        border-right: 1px solid {theme['border_subtle']};
        border-bottom: 1px solid {theme['border']};
    }}

    /* Barra de Ferramentas Matplotlib */
    QToolBar {{
        background-color: transparent;
        border: none;
        spacing: 6px;
        padding: 4px;
    }}
    QToolButton {{
        background-color: {theme['bg_card_alt']};
        border: 1px solid {theme['border']};
        border-radius: 5px;
        padding: 4px 6px;
    }}
    QToolButton:hover {{
        background-color: {theme['bg_hover']};
        border-color: {theme['border_focus']};
    }}

    /* Barra de Rolagem Refinada */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {theme['border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {theme['text_muted']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {theme['border']};
        border-radius: 4px;
        min-width: 20px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {theme['text_muted']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Splitter */
    QSplitter::handle {{
        background-color: {theme['border_subtle']};
        width: 3px;
    }}
    QSplitter::handle:hover {{
        background-color: {theme['accent']};
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {theme['bg_card']};
        color: {theme['text_secondary']};
        border-top: 1px solid {theme['border_subtle']};
        font-size: 11.5px;
        padding: 3px 10px;
    }}

    /* Checkbox & RadioButton */
    QCheckBox, QRadioButton {{
        spacing: 8px;
        font-size: 12px;
        color: {theme['text_primary']};
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 17px;
        height: 17px;
        border: 1.5px solid {theme['border']};
        border-radius: 4px;
        background-color: {theme['bg_input']};
    }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {theme['accent']};
        background-color: {theme['bg_hover']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {theme['accent']};
        border-color: {theme['accent']};
        image: url(assets/icons/check-white.svg);
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    QRadioButton::indicator:checked {{
        background-color: {theme['accent']};
        border: 4px solid {theme['bg_card']};
    }}
    """
