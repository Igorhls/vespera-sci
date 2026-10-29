"""
Ponto de entrada principal da aplicação Desktop Vespera Sci.
Execução: py main.py
"""

import logging
import os
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.paths import configurar_logging, diretorio_recursos
from ui.main_window import VesperaMainWindow

logger = logging.getLogger("vespera")


def _registrar_excecao_nao_tratada(tipo, valor, tb):
    """Erros não tratados vão para o log em vez de desaparecerem (no .exe sem console não há stderr)."""
    if issubclass(tipo, KeyboardInterrupt):
        sys.__excepthook__(tipo, valor, tb)
        return
    logger.critical("Exceção não tratada", exc_info=(tipo, valor, tb))


def main():
    caminho_log = configurar_logging()
    sys.excepthook = _registrar_excecao_nao_tratada
    logger.info("Iniciando Vespera Sci (log: %s)", caminho_log)

    # Desacopla o ícone da barra de tarefas do executável genérico do Python no Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vesperasci.desktop.app.1.0")
        except (AttributeError, OSError):
            logger.debug("Não foi possível definir o AppUserModelID")

    app = QApplication(sys.argv)
    app.setApplicationName("Vespera Sci")
    app.setOrganizationName("VesperaSci")

    icon_path = os.path.join(diretorio_recursos(), "assets", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = VesperaMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
