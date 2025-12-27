#!/bin/bash
set -e

# Define paths
VENV_DIR=".venv"
DIST_DIR="dist"
BUILD_DIR="build"

# Ensure we are in the project directory
cd "$(dirname "$0")"

echo "🚀 Starting build process for QuickTube..."

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "📦 Installing/Updating dependencies..."
pip install -r requirements.txt --quiet

# Clean previous builds
echo "🧹 Cleaning up old build artifacts..."
rm -rf "$DIST_DIR" "$BUILD_DIR"

# Run PyInstaller
echo "🔨 Building executable with PyInstaller..."
# We use the .spec file for configuration
pyinstaller quicktube.spec --clean --log-level=WARN

echo "✅ Build complete!"
echo "📂 Executable is located in: $DIST_DIR/quicktube"

# Optional: verify it runs
if [ -f "$DIST_DIR/quicktube" ]; then
    echo "🧪 Verifying executable..."
    # Just checking file existence for now, as running it requires interactivity
    ls -lh "$DIST_DIR/quicktube"
else
    echo "❌ Error: Executable was not created."
    exit 1
fi
