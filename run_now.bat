@echo off
chcp 65001 >nul
title Microsoft Rewards - Run Now
color 0E

cd /d "%~dp0"

echo.
echo  +===================================================+
echo  ^| Running Bot Now...                                ^|
echo  +===================================================+
echo.

:: Install dependencies silently
py -m pip install -r requirements.txt -q 2>nul

:: Run the bot
py rewards_bot.py --run

pause
