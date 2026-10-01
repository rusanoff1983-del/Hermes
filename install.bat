@echo off
setlocal

echo ========================================================
echo  Hermes Plugins & UI Extensions Installer
echo ========================================================
echo.

python "%~dp0install.py" --install-deps

echo.
echo ========================================================
echo  Installation finished.
echo  Reload Hermes Desktop (Ctrl+K -^> Reload Window).
echo ========================================================
echo.
pause
