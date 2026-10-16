@echo off
chcp 65001 >nul
title Vespera Sci — Iniciando...
cd /d "%~dp0"

REM Verifica se o PySide6 já está instalado; se não estiver, instala as dependências automaticamente
py -c "import PySide6, matplotlib, pandas, openpyxl, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo Instalando dependencias do Vespera Sci pela primeira vez...
    echo ============================================================
    py -m pip install -r requirements.txt
)

REM Inicia a interface desktop sem manter janela de terminal aberta
start "" pyw main.py
if %errorlevel% neq 0 (
    py main.py
)
