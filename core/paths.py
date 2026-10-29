"""
Caminhos de instalação, recursos empacotados e dados do usuário do Vespera Sci.

- Recursos (assets, config, version.json): pasta do código-fonte ou sys._MEIPASS no executável PyInstaller.
- Instalação: pasta do código-fonte, pasta do VesperaSci.exe (Windows) ou o bundle VesperaSci.app (macOS).
- Dados do usuário (projetos salvos, logs): sempre numa pasta gravável do sistema operacional,
  nunca dentro da instalação (Program Files e bundles .app não são graváveis).
"""

import json
import logging
import os
import sys

NOME_APP = "VesperaSci"

logger = logging.getLogger(__name__)


def executando_empacotado() -> bool:
    return bool(getattr(sys, "frozen", False))


def diretorio_codigo_fonte() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def diretorio_recursos() -> str:
    """Pasta que contém assets/, config/ e version.json."""
    if executando_empacotado():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return diretorio_codigo_fonte()


def diretorio_instalacao() -> str:
    """Pasta substituída por uma atualização (no macOS, o próprio VesperaSci.app)."""
    if not executando_empacotado():
        return diretorio_codigo_fonte()
    pasta_exe = os.path.dirname(sys.executable)
    if sys.platform == "darwin":
        # .../VesperaSci.app/Contents/MacOS/VesperaSci -> .../VesperaSci.app
        bundle = os.path.abspath(os.path.join(pasta_exe, "..", ".."))
        if bundle.endswith(".app"):
            return bundle
    return pasta_exe


def diretorio_dados_usuario() -> str:
    """Pasta gravável por usuário (criada sob demanda)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    pasta = os.path.join(base, NOME_APP)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def gravar_json_atomico(caminho: str, dados) -> None:
    """
    Grava JSON num arquivo temporário da mesma pasta e o move por cima do destino.
    Uma queda no meio da gravação nunca deixa o arquivo original truncado.
    """
    pasta = os.path.dirname(os.path.abspath(caminho))
    os.makedirs(pasta, exist_ok=True)
    tmp = f"{caminho}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                logger.warning("Não foi possível remover o temporário %s", tmp)


def configurar_logging() -> str:
    """Envia logs para <dados do usuário>/vespera.log (rotativo) e para o stderr. Retorna o caminho."""
    from logging.handlers import RotatingFileHandler

    caminho_log = os.path.join(diretorio_dados_usuario(), "vespera.log")
    raiz = logging.getLogger()
    if any(getattr(h, "_vespera", False) for h in raiz.handlers):
        return caminho_log

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        arquivo = RotatingFileHandler(caminho_log, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        arquivo.setFormatter(fmt)
        arquivo._vespera = True
        raiz.addHandler(arquivo)
    except OSError:
        pass
    if sys.stderr is not None:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        console._vespera = True
        raiz.addHandler(console)
    raiz.setLevel(logging.INFO)
    return caminho_log
