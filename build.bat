@echo off
title MissAV Downloader Build Script (Windows)
echo 🚀 Starting MissAV Downloader Build Process...

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH.
    pause
    exit /b %errorlevel%
)

:: 2. Create and activate virtual environment
echo 📦 Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate

:: 3. Upgrade pip and install dependencies
echo 📥 Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

:: 4. Check for SpoofDPI binary
if not exist "spoofdpi.exe" (
    echo ⚠️ Warning: spoofdpi.exe not found in project root. 
    echo Please download it from https://github.com/xvzc/SpoofDPI/releases
    pause
)

:: 5. Build the application
echo 🛠️ Running PyInstaller...
pyinstaller --clean MissAV_Downloader_onefile.spec

:: 6. Cleanup
echo 🧹 Cleaning up...
if exist "build" rd /s /q "build"

echo ✅ Build Complete!
echo 📍 Your executable is located in: .\dist\MissAV_Downloader.exe
pause
