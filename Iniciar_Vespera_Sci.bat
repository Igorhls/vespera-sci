@echo off
setlocal
cd /d "%~dp0"
title Vespera Sci

set "PY="
where py >nul 2>&1
if %errorlevel% equ 0 set "PY=py"
if "%PY%"=="" (
    where python >nul 2>&1
    if %errorlevel% equ 0 set "PY=python"
)

if "%PY%"=="" (
    echo [ERRO] Python nao foi encontrado no sistema!
    echo Instale o Python 3.10+ em https://www.python.org e marque "Add python.exe to PATH".
    pause
    exit /b 1
)

%PY% -c "import PySide6, matplotlib, pandas, openpyxl, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo   Instalando dependencias do Vespera Sci pela primeira vez...
    echo ============================================================
    %PY% -m pip install -r requirements.txt
)

where pyw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pyw main.py
    exit /b 0
)

where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw main.py
    exit /b 0
)

start "" %PY% main.py
exit /b 0
