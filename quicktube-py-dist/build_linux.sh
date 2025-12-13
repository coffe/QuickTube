#!/bin/bash
set -e

echo "Bygger QuickTube för Linux..."

# Skapa bin-mapp
mkdir -p bin

# 1. yt-dlp
echo "Laddar ner yt-dlp..."
curl -L -o bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
chmod +x bin/yt-dlp

# 2. svtplay-dl
echo "Laddar ner svtplay-dl..."
curl -L -o bin/svtplay-dl https://svtplay-dl.se/download/latest/svtplay-dl
chmod +x bin/svtplay-dl

# 3. gum
echo "Laddar ner gum..."
curl -L -o gum.tar.gz https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Linux_x86_64.tar.gz
tar -xzf gum.tar.gz
# Försök hitta gum binären i den uppackade mappen
if [ -d "gum_0.13.0_Linux_x86_64" ]; then
    mv gum_0.13.0_Linux_x86_64/gum bin/gum
    rm -rf gum_0.13.0_Linux_x86_64
elif [ -f "gum" ]; then
    mv gum bin/gum
fi
rm gum.tar.gz
chmod +x bin/gum

echo "Binärer klara."

# Installera dependencies
if [ ! -d "venv" ]; then
    echo "Skapar venv..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install pyinstaller

# Bygg
echo "Kör PyInstaller..."
pyinstaller --onefile --clean --add-binary "bin/gum:bin" --add-binary "bin/yt-dlp:bin" --add-binary "bin/svtplay-dl:bin" quicktube.py

echo "Klart! Körbar fil finns i dist/quicktube"
