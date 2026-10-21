#!/bin/bash
# ==============================================================================
# Script de Compilação Local para macOS Intel (ex: MacBook Pro A1708 / Ventura+)
# Gera o aplicativo VesperaSci.app e a imagem de disco instalável .dmg
# Execução no Mac: chmod +x build_macos.sh && ./build_macos.sh
# ==============================================================================

set -e

echo "=== [1/4] Instalando dependências de build ==="
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller pillow

echo "=== [2/4] Gerando ícone oficial .icns para o macOS ==="
mkdir -p AppIcon.iconset
sips -z 16 16     assets/app_icon.png --out AppIcon.iconset/icon_16x16.png
sips -z 32 32     assets/app_icon.png --out AppIcon.iconset/icon_16x16@2x.png
sips -z 32 32     assets/app_icon.png --out AppIcon.iconset/icon_32x32.png
sips -z 64 64     assets/app_icon.png --out AppIcon.iconset/icon_32x32@2x.png
sips -z 128 128   assets/app_icon.png --out AppIcon.iconset/icon_128x128.png
sips -z 256 256   assets/app_icon.png --out AppIcon.iconset/icon_128x128@2x.png
sips -z 256 256   assets/app_icon.png --out AppIcon.iconset/icon_256x256.png
sips -z 512 512   assets/app_icon.png --out AppIcon.iconset/icon_256x256@2x.png
sips -z 512 512   assets/app_icon.png --out AppIcon.iconset/icon_512x512.png
iconutil -c icns AppIcon.iconset -o assets/app_icon.icns
rm -rf AppIcon.iconset

echo "=== [3/4] Compilando Bundle VesperaSci.app via PyInstaller ==="
pyinstaller --noconfirm --onedir --windowed \
  --name "VesperaSci" \
  --icon "assets/app_icon.icns" \
  --add-data "assets:assets" \
  --add-data "config:config" \
  --add-data "version.json:." \
  --osx-bundle-identifier "com.vesperasci.app" \
  main.py

echo "=== [4/4] Gerando imagem de disco .dmg ==="
mkdir -p dmg_root
rm -rf dmg_root/*
cp -r dist/VesperaSci.app dmg_root/
ln -s /Applications dmg_root/Applications
hdiutil create -volname "Vespera Sci" -srcfolder dmg_root -ov -format UDZO dist/VesperaSci-macOS-Intel-x86_64.dmg
rm -rf dmg_root

echo ""
echo "=============================================================================="
echo "  COMPILAÇÃO CONCLUÍDA COM SUCESSO!"
echo "  Arquivo gerado: dist/VesperaSci-macOS-Intel-x86_64.dmg"
echo "=============================================================================="
