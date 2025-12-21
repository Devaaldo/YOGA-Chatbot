"""
Quick launcher for YOGA Chatbot V3 Telegram Bot

Usage:
    python run_telegram_v3.py

Make sure to set TELEGRAM_TOKEN in .env file or environment variable
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Load .env file if exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded .env from {env_path}")
    else:
        print("⚠ .env file not found, using system environment variables")
except ImportError:
    print("⚠ python-dotenv not installed, using system environment variables only")

# Check token
if os.getenv('TELEGRAM_TOKEN') == 'YOUR_TELEGRAM_BOT_TOKEN_HERE' or not os.getenv('TELEGRAM_TOKEN'):
    print("=" * 80)
    print("ERROR: TELEGRAM_TOKEN not set!")
    print("=" * 80)
    print("\nPlease set your Telegram Bot Token first:")
    print("\n  Linux/Mac:")
    print("    export TELEGRAM_TOKEN=\"your_token_here\"")
    print("\n  Windows CMD:")
    print("    set TELEGRAM_TOKEN=your_token_here")
    print("\n  Windows PowerShell:")
    print("    $env:TELEGRAM_TOKEN=\"your_token_here\"")
    print("\nThen run this script again.")
    print()
    sys.exit(1)

# Import and run bot
from telegram_bot_v3 import main

if __name__ == '__main__':
    main()
