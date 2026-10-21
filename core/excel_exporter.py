"""
Exportação de tabelas formatadas e gráficos nativos do Microsoft Excel (.xlsx) via openpyxl.
"""

import io
import numpy as np
import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import pandas as pd

from core.sanitizer import calcular_regressao_linear


def gerar_excel_linhas_bytes(
    df: pd.DataFrame,
    titulo_dia: str,
    titulo_grafico: str,
    min_y: float = None,
    max_y: float = None,
) -> bytes:
    """Gera a planilha Excel (.xlsx) para o gráfico de linhas (Pontos P1..Pn)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dados e Grafico"

    borda_fina = Border(
        left=Side(style="thin", color="A6A6A6"),
        right=Side(style="thin", color="A6A6A6"),
        top=Side(style="thin", color="A6A6A6"),
        bottom=Side(style="thin", color="A6A6A6"),
    )

    ws.merge_cells("B2:E2")
    header = ws.cell(row=2, column=2, value=titulo_dia)
    header.font = Font(name="Times New Roman", size=11, bold=True)
    header.alignment = Alignment(horizontal="center", vertical="center")
    for c in range(2, 6):
        ws.cell(row=2, column=c).border = borda_fina

    colunas = ["Pontos", "Manha", "Tarde", "Noite"]
    for idx, col in enumerate(colunas, start=2):
        c = ws.cell(row=3, column=idx, value=col)
        c.font = Font(name="Times New Roman", size=10, bold=True)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = borda_fina

    for r_idx, row in df.iterrows():
        r = 4 + r_idx
        ws.cell(row=r, column=2, value=str(row["Pontos"])).alignment = Alignment(horizontal="center")
        for col_idx, col_name in enumerate(["Manha", "Tarde", "Noite"], start=3):
            val = row.get(col_name, np.nan)
            cell = ws.cell(row=r, column=col_idx, value=float(val) if pd.notnull(val) else None)
            cell.alignment = Alignment(horizontal="center")
            cell.border = borda_fina
            if cell.value is not None:
                cell.number_format = "0.0"
        ws.cell(row=r, column=2).border = borda_fina

    fim_dados = 3 + len(df)

    chart = LineChart()
    chart.title = titulo_grafico
    chart.style = 10
    chart.y_axis.title = "Temperatura do ar (°C)"
    chart.x_axis.title = "Pontos"
    if min_y is not None:
        chart.y_axis.scaling.min = float(min_y)
    if max_y is not None:
        chart.y_axis.scaling.max = float(max_y)
    chart.y_axis.majorUnit = 2
    chart.width = 16
    chart.height = 9.5

    dados_ref = Reference(ws, min_col=3, min_row=3, max_col=5, max_row=fim_dados)
    cats_ref = Reference(ws, min_col=2, min_row=4, max_row=fim_dados)
    chart.add_data(dados_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    ws.add_chart(chart, "G2")

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 11
    ws.column_dimensions["C"].width = 11
    ws.column_dimensions["D"].width = 11
    ws.column_dimensions["E"].width = 11
    ws.column_dimensions["F"].width = 4

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def gerar_excel_barras_bytes(
    df: pd.DataFrame,
    titulo_tabela: str,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_y: float = None,
    max_y: float = None,
    rotulos_legenda: dict = None,
) -> bytes:
    """
    Gera a planilha Excel (.xlsx) com a tabela de Média e Desvio Padrão (TA) e
    o gráfico de colunas agrupadas ao lado.
    """
    if rotulos_legenda is None:
        rotulos_legenda = {}

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Media e Desvio Padrao"

    borda_preta = Border(
        left=Side(style="thin", color="000000"),
        right=Side(style="thin", color="000000"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="thin", color="000000"),
    )

    ws.merge_cells("B2:F2")
    header = ws.cell(row=2, column=2, value=titulo_tabela or "TA")
    header.font = Font(name="Calibri", size=11, bold=False)
    header.alignment = Alignment(horizontal="center", vertical="center")
    for c in range(2, 7):
        ws.cell(row=2, column=c).border = borda_preta

    cabecalhos_cols = [
        "Mês",
        rotulos_legenda.get("Bosque", "Bosque"),
        rotulos_legenda.get("Desvio_Bosque", "Desvio/p"),
        rotulos_legenda.get("Estacionamento", "Estacionamento"),
        rotulos_legenda.get("Desvio_Estacionamento", "Desvio/p"),
    ]
    for idx, texto_col in enumerate(cabecalhos_cols, start=2):
        c = ws.cell(row=3, column=idx, value=texto_col)
        c.font = Font(name="Times New Roman", size=11, bold=False)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = borda_preta
    ws.row_dimensions[3].height = 28

    cols_internas = ["Bosque", "Desvio_Bosque", "Estacionamento", "Desvio_Estacionamento"]
    for r_idx, row in df.iterrows():
        r = 4 + r_idx
        c_mes = ws.cell(row=r, column=2, value=str(row["Mes"]))
        c_mes.font = Font(name="Times New Roman", size=11)
        c_mes.alignment = Alignment(horizontal="left", vertical="center")
        c_mes.border = borda_preta

        for col_offset, col_name in enumerate(cols_internas, start=3):
            val = row.get(col_name, np.nan)
            cell = ws.cell(row=r, column=col_offset, value=float(val) if pd.notnull(val) else None)
            cell.font = Font(name="Times New Roman", size=11)
            cell.alignment = Alignment(horizontal="right", vertical="center")
            cell.border = borda_preta
            if cell.value is not None:
                cell.number_format = "0.##"

    fim_dados = 3 + len(df)

    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.grouping = "clustered"
    chart.overlap = 0
    chart.title = titulo_grafico if titulo_grafico else None
    chart.y_axis.title = rotulo_y
    chart.x_axis.title = rotulo_x
    if min_y is not None:
        chart.y_axis.scaling.min = float(min_y)
    if max_y is not None:
        chart.y_axis.scaling.max = float(max_y)
    chart.width = 16
    chart.height = 10

    dados_ref = Reference(ws, min_col=3, min_row=3, max_col=6, max_row=fim_dados)
    cats_ref = Reference(ws, min_col=2, min_row=4, max_row=fim_dados)
    chart.add_data(dados_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    ws.add_chart(chart, "H2")

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 4

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def gerar_excel_dispersao_bytes(
    df: pd.DataFrame,
    titulo_tabela: str,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_x: float = None,
    max_x: float = None,
    min_y: float = None,
    max_y: float = None,
) -> bytes:
    """Gera a planilha Excel (.xlsx) com matriz de dados de dispersão e sumário estatístico."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dispersão e R²"

    borda_fina = Border(
        left=Side(style="thin", color="A6A6A6"),
        right=Side(style="thin", color="A6A6A6"),
        top=Side(style="thin", color="A6A6A6"),
        bottom=Side(style="thin", color="A6A6A6"),
    )
    fill_cabecalho = PatternFill(start_color="F2F4F7", end_color="F2F4F7", fill_type="solid")
    fill_destaque = PatternFill(start_color="EBF5FB", end_color="EBF5FB", fill_type="solid")

    # Cabeçalho Principal
    ws.merge_cells("B2:D2")
    header = ws.cell(row=2, column=2, value=titulo_tabela or "Dispersão e Regressão")
    header.font = Font(name="Arial", size=11, bold=True)
    header.alignment = Alignment(horizontal="center", vertical="center")
    for c in range(2, 5):
        ws.cell(row=2, column=c).border = borda_fina

    # Colunas de dados
    col_ponto = "Ponto" if "Ponto" in df.columns else df.columns[0]
    col_x = "X" if "X" in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    col_y = "Y" if "Y" in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[-1])

    c_p = ws.cell(row=3, column=2, value="Ponto")
    c_x = ws.cell(row=3, column=3, value=rotulo_x or "Variável X")
    c_y = ws.cell(row=3, column=4, value=rotulo_y or "Variável Y")
    for cell in (c_p, c_x, c_y):
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = fill_cabecalho
        cell.border = borda_fina

    for r_idx, row in df.iterrows():
        r = 4 + r_idx
        ws.cell(row=r, column=2, value=str(row.get(col_ponto, f"P{r_idx+1}"))).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=2).border = borda_fina

        vx = row.get(col_x, np.nan)
        cell_x = ws.cell(row=r, column=3, value=float(vx) if pd.notnull(vx) else None)
        cell_x.alignment = Alignment(horizontal="center")
        cell_x.border = borda_fina
        if cell_x.value is not None:
            cell_x.number_format = "0.00"

        vy = row.get(col_y, np.nan)
        cell_y = ws.cell(row=r, column=4, value=float(vy) if pd.notnull(vy) else None)
        cell_y.alignment = Alignment(horizontal="center")
        cell_y.border = borda_fina
        if cell_y.value is not None:
            cell_y.number_format = "0.00"

    fim_dados = 3 + len(df)

    # Bloco de Estatísticas e Regressão Linear
    reg = calcular_regressao_linear(df[col_x], df[col_y]) if len(df) >= 2 else {}
    if reg:
        row_stat = fim_dados + 2
        ws.merge_cells(f"B{row_stat}:D{row_stat}")
        st_header = ws.cell(row=row_stat, column=2, value="Sumário Estatístico e Regressão Linear")
        st_header.font = Font(name="Arial", size=10, bold=True, color="1E3A8A")
        st_header.fill = fill_destaque
        st_header.alignment = Alignment(horizontal="left", vertical="center")

        stats_linhas = [
            ("Equação da Reta (y = ax + b)", reg.get("equacao", "-")),
            ("Coeficiente de Determinação (R²)", f"{reg.get('r2_formatado', '-')} ({reg.get('r2', 0)*100:.1f}%)"),
            ("Correlação de Pearson (r)", f"{reg.get('r_formatado', '-')} ({reg.get('forca', '')} {reg.get('direcao', '')})"),
            ("Erro Padrão da Estimativa (Se)", f"{reg.get('se', 0):.4f}".replace(".", ",")),
            ("Observações Válidas (N)", str(reg.get("n", 0))),
            ("Média de X", f"{reg.get('media_x', 0):.2f} (±{reg.get('desvio_x', 0):.2f})".replace(".", ",")),
            ("Média de Y", f"{reg.get('media_y', 0):.2f} (±{reg.get('desvio_y', 0):.2f})".replace(".", ",")),
            ("Interpretação Científica", reg.get("interpretacao", "")),
        ]

        for idx_st, (rot, val) in enumerate(stats_linhas, start=1):
            r_cur = row_stat + idx_st
            ws.cell(row=r_cur, column=2, value=rot).font = Font(name="Arial", size=9, bold=True)
            ws.cell(row=r_cur, column=2).border = borda_fina
            ws.merge_cells(f"C{r_cur}:D{r_cur}")
            c_val = ws.cell(row=r_cur, column=3, value=val)
            c_val.font = Font(name="Arial", size=9)
            c_val.border = borda_fina
            ws.cell(row=r_cur, column=4).border = borda_fina

    # Gráfico de Dispersão Nativo no Excel
    try:
        chart = ScatterChart()
        chart.title = titulo_grafico or "Dispersão X vs Y"
        chart.style = 13
        chart.x_axis.title = rotulo_x or "X"
        chart.y_axis.title = rotulo_y or "Y"
        if min_x is not None:
            chart.x_axis.scaling.min = float(min_x)
        if max_x is not None:
            chart.x_axis.scaling.max = float(max_x)
        if min_y is not None:
            chart.y_axis.scaling.min = float(min_y)
        if max_y is not None:
            chart.y_axis.scaling.max = float(max_y)
        chart.width = 16
        chart.height = 10

        xvalues = Reference(ws, min_col=3, min_row=4, max_row=fim_dados)
        yvalues = Reference(ws, min_col=4, min_row=4, max_row=fim_dados)
        series = Series(yvalues, xvalues, title_from_data=False)
        series.title = "Medições"
        series.marker.symbol = "circle"
        series.marker.graphicalProperties.solidFill = "5B9BD5"
        series.marker.graphicalProperties.line.solidFill = "41719C"
        series.graphicalProperties.line.noFill = True
        chart.series.append(series)
        ws.add_chart(chart, "F2")
    except Exception:
        pass

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 24
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 4

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()



def gerar_excel_boxplot_bytes(
    df: pd.DataFrame,
    titulo_tabela: str,
    titulo_grafico: str,
    rotulo_x: str,
    rotulo_y: str,
    min_y: float = None,
    max_y: float = None,
) -> bytes:
    """Gera planilha Excel (.xlsx) contendo os dados brutos e tabela estatística de quartis/mediana."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dados Boxplot"

    borda_fina = Border(
        left=Side(style="thin", color="A6A6A6"),
        right=Side(style="thin", color="A6A6A6"),
        top=Side(style="thin", color="A6A6A6"),
        bottom=Side(style="thin", color="A6A6A6"),
    )

    ws.merge_cells("B2:E2")
    header = ws.cell(row=2, column=2, value=titulo_tabela or "Distribuição Térmica")
    header.font = Font(name="Times New Roman", size=11, bold=True)
    header.alignment = Alignment(horizontal="center", vertical="center")
    for c in range(2, 6):
        ws.cell(row=2, column=c).border = borda_fina

    cols = list(df.columns)
    for idx, col in enumerate(cols, start=2):
        c = ws.cell(row=3, column=idx, value=str(col))
        c.font = Font(name="Times New Roman", size=10, bold=True)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = borda_fina

    for r_idx, row in df.iterrows():
        r = 4 + r_idx
        for col_idx, col_name in enumerate(cols, start=2):
            val = row.get(col_name, np.nan)
            cell = ws.cell(row=r, column=col_idx, value=float(val) if pd.notnull(val) and isinstance(val, (int, float)) else str(val) if pd.notnull(val) else None)
            cell.alignment = Alignment(horizontal="center")
            cell.border = borda_fina
            if cell.value is not None and isinstance(cell.value, float):
                cell.number_format = "0.0#"

    ws.column_dimensions["A"].width = 3
    for col_letter in ["B", "C", "D", "E", "F"]:
        ws.column_dimensions[col_letter].width = 14

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
