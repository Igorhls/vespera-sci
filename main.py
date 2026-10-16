"""
Ponto de entrada principal da aplicação Desktop Vespera Sci.
Execução: py main.py
"""

import sys
from PySide6.QtWidgets import QApplication

from ui.main_window import VesperaMainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Vespera Sci")
    app.setOrganizationName("VesperaSci")

    window = VesperaMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
