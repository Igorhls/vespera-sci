@echo off
chcp 65001 >nul
title Instalador Vespera Sci Desktop
cd /d "%~dp0"

echo ======================================================================
echo   INSTALADOR LOCAL - VESPERA SCI ALPHA
echo ======================================================================
echo.

set "PY_CMD="
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    echo [AVISO] O Python nao foi encontrado no seu computador!
    echo Para executar o Vespera Sci, e necessario ter o Python 3.10 ou superior instalado.
    pause
    exit /b 1
)

echo [1/2] Verificando e instalando bibliotecas necessarias...
%PY_CMD% -m pip install -r requirements.txt

echo.
echo [2/2] Criando atalho oficial "Vespera Sci Alpha" na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $d 'Vespera Sci Alpha.lnk')); $s.TargetPath = '%~dp0Iniciar_Vespera_Sci.bat'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%~dp0assets\app_icon.ico'; $s.WindowStyle = 7; $s.Description = 'Vespera Sci Alpha - Scientific Studio'; $s.Save()"

echo.
echo ======================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo   Um atalho "Vespera Sci Alpha" foi criado na sua Area de Trabalho.
echo ======================================================================
pause
