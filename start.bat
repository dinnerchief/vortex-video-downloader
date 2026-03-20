@echo off
title VORTEX - Video Downloader
color 0A

echo.
echo  =========================================
echo    VORTEX - Video Downloader Engine
echo  =========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found!
    echo.
    echo  Please install Python from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  [OK] Python found
echo.

:: Install deps silently
echo  Installing / updating dependencies...
python -m pip install flask yt-dlp --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Check ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [WARNING] ffmpeg not found - video merging may not work.
    echo  Download from: https://ffmpeg.org/download.html
    echo  and add it to your PATH for best quality downloads.
    echo.
) else (
    echo  [OK] ffmpeg found
)

echo.
echo  Starting server on http://localhost:7860
echo  Opening browser...
echo.
echo  Press Ctrl+C to stop the server.
echo.

:: Open browser after short delay
start /b cmd /c "timeout /t 2 >nul && start http://localhost:7860"

:: Run Flask
python app.py

pause
