#!/bin/bash

# MissAV Downloader Build Script for Linux and macOS
# This script bundles the application into a single-file executable using PyInstaller.

echo "🚀 Starting MissAV Downloader Build Process..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    exit 1
fi

# 2. Create and activate virtual environment
echo "📦 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install dependencies
echo "📥 Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 4. Check for SpoofDPI binary
OS_TYPE=$(uname -s)
if [ "$OS_TYPE" == "Linux" ]; then
    SPOOF_BINARY="spoofdpi"
    DOWNLOAD_URL="https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh"
elif [ "$OS_TYPE" == "Darwin" ]; then
    SPOOF_BINARY="spoofdpi"
    DOWNLOAD_URL="https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh"
else
    echo "⚠️ Unknown OS: $OS_TYPE"
fi

if [ ! -f "$SPOOF_BINARY" ]; then
    echo "🔍 SpoofDPI binary not found. Attempting to download..."
    curl -fsSL $DOWNLOAD_URL | bash
    # Move from installation dir to project root
    cp ~/.spoofdpi/bin/spoofdpi .
fi

# 5. Build the application
echo "🛠️ Running PyInstaller..."
pyinstaller --clean MissAV_Downloader_onefile.spec

# 6. Cleanup
echo "🧹 Cleaning up..."
# Optional: keep the build folder if needed for debugging
# rm -rf build

echo "✅ Build Complete!"
echo "📍 Your executable is located in: ./dist/MissAV_Downloader"
if [ "$OS_TYPE" == "Darwin" ]; then
    echo "💡 Note for macOS: You may need to grant execution permissions: chmod +x ./dist/MissAV_Downloader"
fi
