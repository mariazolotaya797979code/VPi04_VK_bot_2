@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python не найден. Установите Python 3.10+ с https://www.python.org/downloads/
    echo При установке отметьте "Add python.exe to PATH".
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Создан файл .env — откройте его и вставьте VK_TOKEN и VK_GROUP_ID
    notepad ".env"
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Запускаю бота. Чтобы остановить — Ctrl+C
echo.
python bot.py
pause
