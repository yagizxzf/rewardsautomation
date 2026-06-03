@echo off
chcp 65001 >nul
title Microsoft Rewards - Idle Monitor
color 0B

cd /d "%~dp0"

echo.
echo  +===================================================+
echo  ^| Starting Idle Monitor...                          ^|
echo  ^| Will auto-run after 5 minutes of inactivity       ^|
echo  +===================================================+
echo.

:: Install dependencies silently
py -m pip install -r requirements.txt -q 2>nul

:: Start the monitor
py rewards_bot.py --monitor

pause
