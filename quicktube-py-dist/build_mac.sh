#!/bin/bash
set -e

echo "Bygger QuickTube för macOS..."

# Skapa mapp för mac-binärer
mkdir -p bin_mac

# 1. yt-dlp (Universal/macOS binary)
echo "Laddar ner yt-dlp..."
curl -L -o bin_mac/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos
chmod +x bin_mac/yt-dlp

# 2. svtplay-dl
echo "Laddar ner svtplay-dl..."
curl -L -o svtplay-dl.zip https://github.com/spaam/svtplay-dl/releases/latest/download/svtplay-dl.zip
unzip -o svtplay-dl.zip -d bin_mac/

# Hitta och flytta binären (oavsett mappstruktur i zip)
find bin_mac -type f -name "svtplay-dl" -exec mv {} bin_mac/svtplay-dl_temp \;

if [ -f "bin_mac/svtplay-dl_temp" ]; then
    mv bin_mac/svtplay-dl_temp bin_mac/svtplay-dl
    chmod +x bin_mac/svtplay-dl
    echo "Hittade och förberedde svtplay-dl."
else
    echo "VARNING: Kunde inte hitta 'svtplay-dl' binär i zip-filen. Bygget kan sakna den."
fi
rm svtplay-dl.zip
# Städa upp ev mappar från zip (men spara yt-dlp som vi redan lagt där)
find bin_mac -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +

# 3. gum
ARCH=$(uname -m)
if [ "$ARCH" == "arm64" ]; then
    echo "Detekterade Apple Silicon (arm64). Laddar ner gum för arm64..."
    curl -L -o gum.tar.gz https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Darwin_arm64.tar.gz
else
    echo "Detekterade Intel (x86_64). Laddar ner gum för x86_64..."
    curl -L -o gum.tar.gz https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Darwin_x86_64.tar.gz
fi

tar -xzf gum.tar.gz -C bin_mac/
# Gum ligger ofta i en undermapp i tar-filen, vi måste hitta och flytta den.
# Hitta filen 'gum' (exkludera mappar) och flytta den till bin_mac root
find bin_mac -type f -name "gum" -exec mv {} bin_mac/gum_temp \;
mv bin_mac/gum_temp bin_mac/gum
rm gum.tar.gz
# Städa upp undermappar
find bin_mac -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
chmod +x bin_mac/gum

echo "Alla binärer nedladdade till bin_mac/."

# Installera pyinstaller om det saknas
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller saknas. Installerar..."
    pip3 install pyinstaller
fi

echo "Startar PyInstaller..."
# Notera: På macOS används ':' som separator precis som på Linux.
pyinstaller --onefile --name quicktube-mac --add-binary "bin_mac/gum:bin" --add-binary "bin_mac/yt-dlp:bin" --add-binary "bin_mac/svtplay-dl:bin" quicktube.py

echo "Klart! Appen ligger i dist/quicktube-mac"
