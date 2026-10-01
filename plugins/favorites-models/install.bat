@echo off
setlocal

echo ========================================================
echo  Installing Favorites Models Plugin for Hermes Desktop
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
