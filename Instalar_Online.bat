@echo off
chcp 65001 >nul
title Instalador Online - Vespera Sci Alpha

echo ======================================================================
echo   VESPERA SCI ALPHA - INSTALADOR OFICIAL
echo   Repositorio: https://github.com/Igorhls/vespera-sci
echo ======================================================================
echo.

set "DESTINO=%LOCALAPPDATA%\VesperaSci"
set "URL_ZIP=https://github.com/Igorhls/vespera-sci/archive/refs/heads/main.zip"
set "TEMP_DIR=%TEMP%\vespera_install_%RANDOM%"
set "TEMP_ZIP=%TEMP_DIR%\main.zip"

if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

echo [1/4] Verificando ambiente Python...
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
    echo.
    echo [AVISO] O Python nao foi encontrado no seu computador!
    echo Para executar o Vespera Sci, e necessario instalar o Python 3.10 ou superior.
    echo.
    echo Abrindo a pagina oficial de download do Python no navegador...
    start https://www.python.org/downloads/
    echo.
    echo ATENCAO AO INSTALAR: Na primeira tela do instalador, marque a caixa:
    echo   [X] Add python.exe to PATH
    echo.
    pause
    exit /b 1
)

echo Python detectado: %PY_CMD%

echo.
echo [2/4] Baixando versao mais recente do GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%URL_ZIP%', '%TEMP_ZIP%')"

if not exist "%TEMP_ZIP%" (
    echo [ERRO] Nao foi possivel baixar o arquivo do GitHub.
    echo Verifique sua conexao com a internet ou firewall.
    pause
    exit /b 1
)

echo.
echo [3/4] Instalando arquivos em "%DESTINO%"...
if not exist "%DESTINO%" mkdir "%DESTINO%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%TEMP_ZIP%' -DestinationPath '%TEMP_DIR%\unpacked' -Force; Copy-Item -Path '%TEMP_DIR%\unpacked\vespera-sci-main\*' -Destination '%DESTINO%' -Recurse -Force"

echo.
echo [4/4] Instalando dependencias cientificas...
echo Aguarde, configurando PySide6, Matplotlib, Pandas, NumPy, OpenPyXL...
%PY_CMD% -m pip install -r "%DESTINO%\requirements.txt"

echo.
echo Criando atalho oficial Vespera Sci Alpha na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $d 'Vespera Sci Alpha.lnk')); $s.TargetPath = (Join-Path '%DESTINO%' 'Iniciar_Vespera_Sci.bat'); $s.WorkingDirectory = '%DESTINO%'; $s.IconLocation = (Join-Path '%DESTINO%' 'assets\app_icon.ico'); $s.WindowStyle = 7; $s.Description = 'Vespera Sci Alpha - Scientific Studio'; $s.Save()"

:: Limpeza dos temporarios
rd /s /q "%TEMP_DIR%" >nul 2>&1

echo.
echo ======================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo   O atalho foi criado na sua Area de Trabalho.
echo ======================================================================
echo.
echo Deseja abrir o Vespera Sci agora? (S/N)
set /p ABRIR="> "
if /i "%ABRIR%"=="S" (
    start "" "%DESTINO%\Iniciar_Vespera_Sci.bat"
)
