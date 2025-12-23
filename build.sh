#!/bin/bash
set -e

# Define colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building QuickTube 2.0 Suite...${NC}"

# Cleanup
echo "Cleaning up old builds..."
rm -rf build dist .venv *.spec

# Create Virtual Environment
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build QuickTube
echo "Compiling QuickTube..."
pyinstaller --onefile --name quicktube --clean quicktube.py

# Build YTRSS
echo "Compiling YTRSS..."
pyinstaller --onefile --name ytrss --add-data "KEYS.md:." --clean ytrss.py

# Organize output
mkdir -p bin
cp dist/quicktube bin/
cp dist/ytrss bin/

echo -e "${GREEN}Build complete! Binaries located in: bin/${NC}"