@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo  Installing Hermes Antigravity Direct Plugin
echo ========================================================

set TARGET_DIR=%LOCALAPPDATA%\hermes\plugins\antigravity-direct
if not exist "%TARGET_DIR%" (
    echo [*] Creating plugin directory: %TARGET_DIR%
    mkdir "%TARGET_DIR%"
)

echo [*] Copying plugin files...
copy /Y "%~dp0plugin.yaml" "%TARGET_DIR%\" >nul
copy /Y "%~dp0__init__.py" "%TARGET_DIR%\" >nul
copy /Y "%~dp0direct.py" "%TARGET_DIR%\" >nul
copy /Y "%~dp0wire.mjs" "%TARGET_DIR%\" >nul
copy /Y "%~dp0package.json" "%TARGET_DIR%\" >nul

cd /d "%TARGET_DIR%"
echo [*] Installing Node.js dependencies...
call npm install --no-audit --no-fund

echo.
echo ========================================================
echo  Plugin successfully installed!
echo.
echo  Next steps:
echo   1. Authenticate via your Google account in browser:
echo        hermes auth add antigravity-direct
echo.
echo   2. Run a chat session with Gemini:
echo        hermes chat --provider antigravity-direct -m gemini-3.7-flash-medium
echo ========================================================
echo.
pause
