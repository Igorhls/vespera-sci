"""
Exportação de tabelas formatadas e gráficos nativos do Microsoft Excel (.xlsx) via openpyxl.
"""

import io
import numpy as np
import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, Side
import pandas as pd


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
