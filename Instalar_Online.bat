@echo off
chcp 65001 >nul
title Instalador Online — Vespera Sci Alpha
cd /d "%~dp0"

echo ======================================================================
echo   VESPERA SCI ALPHA — INSTALADOR VIA GITHUB
echo   Repositorio Oficial: https://github.com/Igorhls/vespera-sci
echo ======================================================================
echo.

set "DESTINO=%LOCALAPPDATA%\VesperaSci"
set "URL_ZIP=https://github.com/Igorhls/vespera-sci/archive/refs/heads/main.zip"
set "TEMP_ZIP=%TEMP%\vespera_sci_main.zip"

echo [1/4] Baixando versao mais recente do GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
  "Invoke-WebRequest -Uri '%URL_ZIP%' -OutFile '%TEMP_ZIP%'"

if not exist "%TEMP_ZIP%" (
    echo [ERRO] Nao foi possivel baixar o pacote do GitHub. Verifique sua conexao com a internet.
    pause
    exit /b 1
)

echo.
echo [2/4] Extraindo arquivos em "%DESTINO%"...
if not exist "%DESTINO%" mkdir "%DESTINO%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP%\vespera_temp' -Force; " ^
  "Copy-Item -Path '%TEMP%\vespera_temp\vespera-sci-main\*' -Destination '%DESTINO%' -Recurse -Force; " ^
  "Remove-Item -Path '%TEMP%\vespera_temp' -Recurse -Force; " ^
  "Remove-Item -Path '%TEMP_ZIP%' -Force"

echo.
echo [3/4] Verificando e instalando dependencias (PySide6, Matplotlib, Pandas)...
py -m pip install -r "%DESTINO%\requirements.txt" >nul 2>&1
if %errorlevel% neq 0 (
    echo Tentando com python direto...
    python -m pip install -r "%DESTINO%\requirements.txt"
)

echo.
echo [4/4] Criando atalho oficial na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$WshShell = New-Object -ComObject WScript.Shell; " ^
  "$Desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop 'Vespera Sci Alpha.lnk')); " ^
  "$Shortcut.TargetPath = (Join-Path '%DESTINO%' 'Iniciar_Vespera_Sci.bat'); " ^
  "$Shortcut.WorkingDirectory = '%DESTINO%'; " ^
  "$Shortcut.IconLocation = (Join-Path '%DESTINO%' 'assets\app_icon.ico'); " ^
  "$Shortcut.WindowStyle = 7; " ^
  "$Shortcut.Description = 'Vespera Sci Alpha — Scientific Plotting & Data Studio'; " ^
  "$Shortcut.Save()"

echo.
echo ======================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo   Um atalho "Vespera Sci Alpha" foi criado na sua Area de Trabalho.
echo ======================================================================
echo.
echo Deseja iniciar o Vespera Sci agora? (S/N)
set /p ABRIR="> "
if /i "%ABRIR%"=="S" (
    start "" "%DESTINO%\Iniciar_Vespera_Sci.bat"
)
