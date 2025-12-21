#!/bin/bash
set -e

echo "Building QuickTube for macOS..."

# Create directory for mac binaries
mkdir -p bin_mac

# 1. yt-dlp (Universal/macOS binary)
echo "Downloading yt-dlp..."
curl -L -o bin_mac/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos
chmod +x bin_mac/yt-dlp

# 2. svtplay-dl
echo "Downloading svtplay-dl..."
curl -L -o svtplay-dl.zip https://github.com/spaam/svtplay-dl/releases/latest/download/svtplay-dl.zip
unzip -o svtplay-dl.zip -d bin_mac/

# Find and move the binary (regardless of folder structure in zip)
find bin_mac -type f -name "svtplay-dl" -exec mv {} bin_mac/svtplay-dl_temp \;

if [ -f "bin_mac/svtplay-dl_temp" ]; then
    mv bin_mac/svtplay-dl_temp bin_mac/svtplay-dl
    chmod +x bin_mac/svtplay-dl
    echo "Found and prepared svtplay-dl."
else
    echo "WARNING: Could not find 'svtplay-dl' binary in zip file. Build might be missing it."
fi
rm svtplay-dl.zip
# Clean up any folders from zip (but save yt-dlp which we already put there)
find bin_mac -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +

# 3. gum
ARCH=$(uname -m)
if [ "$ARCH" == "arm64" ]; then
    echo "Detected Apple Silicon (arm64). Downloading gum for arm64..."
    curl -L -o gum.tar.gz https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Darwin_arm64.tar.gz
else
    echo "Detected Intel (x86_64). Downloading gum for x86_64..."
    curl -L -o gum.tar.gz https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Darwin_x86_64.tar.gz
fi

tar -xzf gum.tar.gz -C bin_mac/
# Gum is often in a subfolder in the tar file, we must find and move it.
# Find the file 'gum' (exclude directories) and move it to bin_mac root
find bin_mac -type f -name "gum" -exec mv {} bin_mac/gum_temp \;
mv bin_mac/gum_temp bin_mac/gum
rm gum.tar.gz
# Clean up subfolders
find bin_mac -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
chmod +x bin_mac/gum

echo "All binaries downloaded to bin_mac/."

# Install pyinstaller if missing
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller missing. Installing..."
    pip3 install pyinstaller
fi

echo "Starting PyInstaller..."
# Note: On macOS ':' is used as separator just like on Linux.
pyinstaller --onefile --name quicktube-mac --add-binary "bin_mac/gum:bin" --add-binary "bin_mac/yt-dlp:bin" --add-binary "bin_mac/svtplay-dl:bin" quicktube.py

echo "Done! App is located in dist/quicktube-mac"
