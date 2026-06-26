@echo off
REM YOGA Chatbot - one-click local launcher (Windows cmd)
REM Activates the venv if present, sets PYTHONPATH, and starts the bot.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

set PYTHONPATH=src

echo Starting YOGA Chatbot... (Ctrl+C to stop)
python -m yoga_chatbot.bot.bot

pause
