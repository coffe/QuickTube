#!/bin/bash
set -e

echo "Building QuickTube for Linux..."

# Create bin directory
mkdir -p bin

# 1. yt-dlp
echo "Downloading yt-dlp..."
curl -L -o bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
chmod +x bin/yt-dlp

# 2. svtplay-dl
echo "Downloading svtplay-dl..."
curl -L -o bin/svtplay-dl https://svtplay-dl.se/download/latest/svtplay-dl
chmod +x bin/svtplay-dl

# 3. gum
echo "Downloading gum..."
curl -L -o gum.tar.gz https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Linux_x86_64.tar.gz
tar -xzf gum.tar.gz
# Try to find the gum binary in the extracted folder
if [ -d "gum_0.13.0_Linux_x86_64" ]; then
    mv gum_0.13.0_Linux_x86_64/gum bin/gum
    rm -rf gum_0.13.0_Linux_x86_64
elif [ -f "gum" ]; then
    mv gum bin/gum
fi
rm gum.tar.gz
chmod +x bin/gum

echo "Binaries ready."

# Install dependencies
if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install pyinstaller

# Build
echo "Running PyInstaller..."
pyinstaller --onefile --clean --add-binary "bin/gum:bin" --add-binary "bin/yt-dlp:bin" --add-binary "bin/svtplay-dl:bin" quicktube.py

echo "Done! Executable found in dist/quicktube"
