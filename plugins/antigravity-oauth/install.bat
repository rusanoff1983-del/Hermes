@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ========================================================
echo   Установка плагина Google Antigravity Direct (Gemini)
echo ========================================================
echo.

set TARGET_DIR=%LOCALAPPDATA%\hermes\plugins\antigravity-direct
if not exist "%TARGET_DIR%" (
    echo [*] Создание папки плагина: %TARGET_DIR%
    mkdir "%TARGET_DIR%"
)

echo [*] Копирование файлов плагина...
copy /Y "%~dp0plugin.yaml" "%TARGET_DIR%\" >nul
copy /Y "%~dp0__init__.py" "%TARGET_DIR%\" >nul
copy /Y "%~dp0direct.py" "%TARGET_DIR%\" >nul
copy /Y "%~dp0wire.mjs" "%TARGET_DIR%\" >nul
copy /Y "%~dp0package.json" "%TARGET_DIR%\" >nul

cd /d "%TARGET_DIR%"
echo [*] Установка необходимых библиотек Node.js...
call npm install --no-audit --no-fund

echo.
echo ========================================================
echo   Плагин успешно установлен в Hermes!
echo ========================================================
echo.
set /p DO_AUTH="Авторизоваться в Google прямо сейчас через браузер? (Y/N, Enter = Да): "
if /i "%DO_AUTH%"=="N" goto finish

echo.
echo [*] Запуск авторизации Google в браузере...
call hermes auth add antigravity-direct

:finish
echo.
echo ========================================================
echo   Готово! Для запуска чата с Gemini:
echo   hermes chat --provider antigravity-direct -m gemini-3.7-flash-medium
echo ========================================================
echo.
pause
