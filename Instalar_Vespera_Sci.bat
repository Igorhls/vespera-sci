@echo off
setlocal
cd /d "%~dp0"
title Instalador Local - Vespera Sci

echo ======================================================================
echo   INSTALADOR LOCAL - VESPERA SCI
echo ======================================================================
echo.

set "PY="
where py >nul 2>&1
if %errorlevel% equ 0 set "PY=py"
if "%PY%"=="" (
    where python >nul 2>&1
    if %errorlevel% equ 0 set "PY=python"
)

if "%PY%"=="" (
    echo [AVISO] Python nao foi encontrado no seu computador!
    echo Instale o Python 3.10+ em https://www.python.org marcando "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/2] Verificando e instalando bibliotecas necessarias...
%PY% -m pip install -r requirements.txt

echo.
echo [2/2] Criando atalho oficial "Vespera Sci" na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $d 'Vespera Sci.lnk')); $s.TargetPath = (Join-Path '%~dp0' 'Iniciar_Vespera_Sci.bat'); $s.WorkingDirectory = '%~dp0'; $s.IconLocation = (Join-Path '%~dp0' 'assets\app_icon.ico'); $s.WindowStyle = 7; $s.Description = 'Vespera Sci'; $s.Save()"

echo.
echo ======================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo   Um atalho "Vespera Sci" foi criado na sua Area de Trabalho.
echo ======================================================================
pause
