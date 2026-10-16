"""
Widget de edição tabular de dados experimentais (Linhas P1..Pn e Barras TA),
incluindo importador de blocos copiados do Excel, calculadora rápida de Média/Desvio Padrão
e sumário estatístico descritivo em tempo real.
"""

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
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


class DataTableWidget(QWidget):
    """Painel central de entrada e edição de dados tabulares, metadados de eixos e estatísticas."""

    dataOrMetaChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self.tipo_grafico = "linhas"
        self.df_linhas = pd.DataFrame(columns=["Pontos", "Manha", "Tarde", "Noite"])
        self.df_barras = pd.DataFrame(
            columns=["Mes", "Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
        )

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        self.lbl_secao = QLabel("<b>Matriz de Dados Experimentais (Pontos P1–Pn)</b>")
        self.lbl_secao.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.lbl_secao)

        # -------------------------------------------------------------------
        # 1. Metadados do Gráfico (Títulos, Eixos e Limites Y)
        # -------------------------------------------------------------------
        grp_meta = QGroupBox("Identificadores, Rótulos dos Eixos e Limites da Escala")
        grid_meta = QGridLayout(grp_meta)
        grid_meta.setContentsMargins(10, 10, 10, 10)
        grid_meta.setHorizontalSpacing(10)
        grid_meta.setVerticalSpacing(6)

        self.lbl_tit_dia = QLabel("Identificador / Dia:")
        self.txt_titulo_dia = QLineEdit()
        self.txt_titulo_dia.textChanged.connect(self._on_meta_changed)

        self.lbl_tit_graf = QLabel("Título do Gráfico:")
        self.txt_titulo_grafico = QLineEdit()
        self.txt_titulo_grafico.setPlaceholderText("Deixe vazio para padrão sem título superior")
        self.txt_titulo_grafico.textChanged.connect(self._on_meta_changed)

        grid_meta.addWidget(self.lbl_tit_dia, 0, 0)
        grid_meta.addWidget(self.txt_titulo_dia, 0, 1)
        grid_meta.addWidget(self.lbl_tit_graf, 0, 2)
        grid_meta.addWidget(self.txt_titulo_grafico, 0, 3)

        self.txt_rotulo_x = QLineEdit()
        self.txt_rotulo_x.textChanged.connect(self._on_meta_changed)
        self.txt_rotulo_y = QLineEdit()
        self.txt_rotulo_y.textChanged.connect(self._on_meta_changed)

        grid_meta.addWidget(QLabel("Legenda Eixo X:"), 1, 0)
        grid_meta.addWidget(self.txt_rotulo_x, 1, 1)
        grid_meta.addWidget(QLabel("Legenda Eixo Y:"), 1, 2)
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

        grid_meta.addWidget(QLabel("Y Mínimo:"), 2, 0)
        grid_meta.addWidget(self.spn_min_y, 2, 1)
        grid_meta.addWidget(QLabel("Y Máximo:"), 2, 2)
        grid_meta.addWidget(self.spn_max_y, 2, 3)

        layout.addWidget(grp_meta)

        # -------------------------------------------------------------------
        # 2. Personalização dos Nomes das Colunas na Legenda (Modo Barras)
        # -------------------------------------------------------------------
        self.grp_rotulos_barras = QGroupBox("Personalizar Nomes das Séries na Tabela e Legenda")
        rb_layout = QHBoxLayout(self.grp_rotulos_barras)
        rb_layout.setContentsMargins(10, 8, 10, 8)
        self.txt_rs1 = QLineEdit("Bosque")
        self.txt_rs2 = QLineEdit("Desvio/p")
        self.txt_rs3 = QLineEdit("Estacionamento")
        self.txt_rs4 = QLineEdit("Desvio/p")
        for lbl_txt, w_edit in [
            ("Série 1:", self.txt_rs1),
            ("Série 2:", self.txt_rs2),
            ("Série 3:", self.txt_rs3),
            ("Série 4:", self.txt_rs4),
        ]:
            rb_layout.addWidget(QLabel(lbl_txt))
            rb_layout.addWidget(w_edit)
            w_edit.textChanged.connect(self._on_rotulos_barras_changed)
        self.grp_rotulos_barras.setVisible(False)
        layout.addWidget(self.grp_rotulos_barras)

        # -------------------------------------------------------------------
        # 3. Ferramenta para Colar Bloco do Excel (Expansível)
        # -------------------------------------------------------------------
        self.btn_toggle_paste = QPushButton("📋 Importar Bloco de Dados do Excel (Copiar e Colar) ▾")
        self.btn_toggle_paste.setCheckable(True)
        self.btn_toggle_paste.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_paste.toggled.connect(self._toggle_paste_box)
        layout.addWidget(self.btn_toggle_paste)

        self.grp_paste = QGroupBox("Colar Células Copiadas do Excel (Ctrl+C -> Ctrl+V)")
        paste_layout = QVBoxLayout(self.grp_paste)
        paste_layout.setContentsMargins(10, 8, 10, 8)

        self.lbl_paste_hint = QLabel(
            "Copie as células no Excel e cole abaixo. As vírgulas decimais são convertidas automaticamente."
        )
        self.lbl_paste_hint.setWordWrap(True)
        paste_layout.addWidget(self.lbl_paste_hint)

        hl_dest = QHBoxLayout()
        self.lbl_destino = QLabel("Destino dos dados:")
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
        paste_layout.addLayout(hl_dest)

        self.txt_paste = QPlainTextEdit()
        self.txt_paste.setPlaceholderText("Cole aqui os valores copiados do Excel...")
        self.txt_paste.setMaximumHeight(90)
        paste_layout.addWidget(self.txt_paste)

        btn_aplicar_paste = QPushButton("✅ Aplicar Dados na Tabela")
        btn_aplicar_paste.setCursor(Qt.PointingHandCursor)
        btn_aplicar_paste.clicked.connect(self._aplicar_colagem_excel)
        paste_layout.addWidget(btn_aplicar_paste)

        self.grp_paste.setVisible(False)
        layout.addWidget(self.grp_paste)

        # -------------------------------------------------------------------
        # 4. Tabela Editável Principal + Barra de Ações da Tabela
        # -------------------------------------------------------------------
        hl_table_btns = QHBoxLayout()
        self.btn_add_row = QPushButton("➕ Nova Linha")
        self.btn_add_row.clicked.connect(self._adicionar_linha)

        self.btn_del_row = QPushButton("➖ Remover Linha")
        self.btn_del_row.clicked.connect(self._remover_linha)

        self.btn_renum = QPushButton("🔢 Renumerar P1..Pn")
        self.btn_renum.clicked.connect(self._renumerar_pontos)

        self.btn_padronizar = QPushButton("🧹 Padronizar Decimais")
        self.btn_padronizar.clicked.connect(self._padronizar_decimais)

        hl_table_btns.addWidget(self.btn_add_row)
        hl_table_btns.addWidget(self.btn_del_row)
        hl_table_btns.addWidget(self.btn_renum)
        hl_table_btns.addWidget(self.btn_padronizar)
        layout.addLayout(hl_table_btns)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemChanged.connect(self._on_table_item_changed)
        layout.addWidget(self.table, stretch=1)

        # -------------------------------------------------------------------
        # 5. Calculadora Auxiliar de Média e Desvio Padrão
        # -------------------------------------------------------------------
        grp_calc = QGroupBox("🧮 Calculadora Rápida de Média e Desvio Padrão Amostral")
        calc_layout = QVBoxLayout(grp_calc)
        calc_layout.setContentsMargins(10, 8, 10, 8)
        self.txt_calc_input = QLineEdit()
        self.txt_calc_input.setPlaceholderText("Digite ou cole valores separados por espaço ou ';' (ex: 26,2 26,5 26,9 27,2)")
        self.txt_calc_input.textChanged.connect(self._atualizar_calculadora)
        self.lbl_calc_result = QLabel("Digite ao menos 2 valores acima para calcular Média e Desvio Padrão.")
        self.lbl_calc_result.setStyleSheet("color: #2c3e50; font-size: 12px;")
        calc_layout.addWidget(self.txt_calc_input)
        calc_layout.addWidget(self.lbl_calc_result)
        layout.addWidget(grp_calc)

        # -------------------------------------------------------------------
        # 6. Sumário Estatístico Descritivo
        # -------------------------------------------------------------------
        grp_stats = QGroupBox("📊 Sumário Estatístico Descritivo das Medições")
        stats_layout = QVBoxLayout(grp_stats)
        stats_layout.setContentsMargins(10, 8, 10, 8)
        self.lbl_stats = QLabel()
        self.lbl_stats.setWordWrap(True)
        self.lbl_stats.setTextInteractionFlags(Qt.TextSelectableByMouse)
        stats_layout.addWidget(self.lbl_stats)
        layout.addWidget(grp_stats)

    def _toggle_paste_box(self, checked: bool):
        self.grp_paste.setVisible(checked)
        self.btn_toggle_paste.setText(
            "📋 Importar Bloco de Dados do Excel (Copiar e Colar) ▴"
            if checked
            else "📋 Importar Bloco de Dados do Excel (Copiar e Colar) ▾"
        )

    def configurar_modo(self, tipo_grafico: str):
        """Alterna o layout da tabela entre 'linhas' e 'barras'."""
        self._updating_ui = True
        self.tipo_grafico = tipo_grafico
        is_linhas = tipo_grafico == "linhas"

        self.grp_rotulos_barras.setVisible(not is_linhas)
        self.lbl_destino.setVisible(is_linhas)
        self.cmb_destino_colar.setVisible(is_linhas)

        if is_linhas:
            self.lbl_secao.setText("<b>Matriz de Dados Experimentais (Pontos P1–Pn)</b>")
            self.lbl_tit_dia.setText("Identificador / Dia:")
            self.btn_renum.setText("🔢 Renumerar P1..Pn")
            self.txt_paste.setPlaceholderText("Cole aqui os dados copiados do Excel...")
        else:
            self.lbl_secao.setText("<b>Tabela de Média e Desvio Padrão (TA)</b>")
            self.lbl_tit_dia.setText("Cabeçalho / Variável:")
            self.btn_renum.setText("🔄 Restaurar Modelo TA")
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

        self.txt_rs1.setText(str(cfg.get("rotulo_s1", "Bosque")))
        self.txt_rs2.setText(str(cfg.get("rotulo_s2", "Desvio/p")))
        self.txt_rs3.setText(str(cfg.get("rotulo_s3", "Estacionamento")))
        self.txt_rs4.setText(str(cfg.get("rotulo_s4", "Desvio/p")))
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
            "rotulo_s1": self.txt_rs1.text() or "Bosque",
            "rotulo_s2": self.txt_rs2.text() or "Desvio/p",
            "rotulo_s3": self.txt_rs3.text() or "Estacionamento",
            "rotulo_s4": self.txt_rs4.text() or "Desvio/p",
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
                f"<b>N:</b> {est['n']}"
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
                            f"<b>{label}:</b> Média = {est['media']:.2f} °C | "
                            f"Desvio (s) = {est['desvio']:.2f} °C | "
                            f"Mín = {est['minimo']:.1f} °C | Máx = {est['maximo']:.1f} °C | "
                            f"Amplitude = {est['amplitude']:.1f} °C"
                        )
            self.lbl_stats.setText("<br>".join(blocos) if blocos else "Sem dados numéricos na tabela.")
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
                linhas_txt.append(f"<b>{mes}:</b> {r1} = {vb} (±{db}) &nbsp;|&nbsp; {r3} = {ve} (±{de})")
            self.lbl_stats.setText("<br>".join(linhas_txt) if linhas_txt else "Sem dados na tabela.")
