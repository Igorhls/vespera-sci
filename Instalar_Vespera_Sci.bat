@echo off
chcp 65001 >nul
title Instalador Vespera Sci Desktop
cd /d "%~dp0"

echo ======================================================================
echo   INSTALADOR LOCAL — VESPERA SCI (SCIENTIFIC PLOTTING STUDIO)
echo ======================================================================
echo.
echo [1/2] Verificando e instalando bibliotecas necessarias...
py -m pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo Tentando com python direto...
    python -m pip install -r requirements.txt
)

echo.
echo [2/2] Criando atalho "Vespera Sci" na Area de Trabalho com o icone oficial...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$WshShell = New-Object -ComObject WScript.Shell; " ^
  "$Desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop 'Vespera Sci.lnk')); " ^
  "$Shortcut.TargetPath = '%~dp0Iniciar_Vespera_Sci.bat'; " ^
  "$Shortcut.WorkingDirectory = '%~dp0'; " ^
  "$Shortcut.IconLocation = '%~dp0assets\app_icon.ico'; " ^
  "$Shortcut.WindowStyle = 7; " ^
  "$Shortcut.Description = 'Vespera Sci Alpha — Scientific Plotting & Data Studio'; " ^
  "$Shortcut.Save()"

echo.
echo ======================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo   Um atalho "Vespera Sci" foi criado na sua Area de Trabalho.
echo ======================================================================
pause
