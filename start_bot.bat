@echo off
chcp 65001 >nul
title Microsoft Rewards Bot
color 0A

echo.
echo  +===================================================+
echo  ^| Microsoft Rewards Daily Task Automation          ^|
echo  +===================================================+
echo.

cd /d "%~dp0"

:: Check if Python is installed
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python.
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install required packages
echo [*] Checking dependencies...
py -m pip install -r requirements.txt -q

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║  1. Idle Monitor (wait 5 min, auto-run)              ║
echo  ║  2. Run Now (start immediately)                      ║
echo  ║  3. Reset State                                      ║
echo  ║  4. Exit                                             ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

choice /c 1234 /n /m "Your choice (1-4): "

if %errorlevel%==1 (
    echo.
    echo [*] Starting Idle Monitor...
    py rewards_bot.py --monitor
)
if %errorlevel%==2 (
    echo.
    echo [*] Running bot now...
    py rewards_bot.py --run
)
if %errorlevel%==3 (
    echo.
    py rewards_bot.py --reset
)
if %errorlevel%==4 (
    echo.
    echo Goodbye!
    exit /b 0
)

pause
