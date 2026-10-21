"""
Ponto de entrada principal da aplicação Desktop Vespera Sci.
Execução: py main.py
"""

import os
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import VesperaMainWindow


def main():
    # Desacopla o ícone da barra de tarefas do executável genérico do Python no Windows
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vesperasci.desktop.app.1.0")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Vespera Sci")
    app.setOrganizationName("VesperaSci")

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = VesperaMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
