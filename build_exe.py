"""
Script utilitário para empacotar o Vespera Sci em um executável Windows (.exe) via PyInstaller.
Uso: py build_exe.py
"""

import subprocess
import sys


def build():
    print("=" * 65)
    print("Empacotando Vespera Sci em executável Windows (.exe)...")
    print("=" * 65)

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "VesperaSci",
        "--add-data",
        "version.json;.",
        "--add-data",
        "config;config",
        "--add-data",
        "core;core",
        "--add-data",
        "ui;ui",
        "main.py",
    ]

    subprocess.check_call(cmd)
    print("\n" + "=" * 65)
    print("Build concluído! O executável encontra-se em: dist/VesperaSci/VesperaSci.exe")
    print("=" * 65)


if __name__ == "__main__":
    build()
