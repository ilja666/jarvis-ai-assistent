#!/usr/bin/env python3
"""
Jarvis Home Agent - Main Entry Point

This script starts both the FastAPI server and the Telegram bot.
You can also run them separately:
- API only: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
- Telegram only: python -m app.telegram_bot
"""

import asyncio
import threading
import signal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def run_api_server():
    """Run the FastAPI server."""
    import uvicorn
    from app.core.config import settings
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )


def run_telegram_bot():
    """Run the Telegram bot."""
    from app.telegram_bot import run_telegram_bot as start_bot
    start_bot()


def main():
    """Main entry point - runs both API server and Telegram bot."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                    JARVIS HOME AGENT                      ║
    ║              Personal AI Assistant v1.0.0                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    mode = os.environ.get("JARVIS_MODE", "both").lower()
    
    if mode == "api":
        print("Starting API server only...")
        run_api_server()
    
    elif mode == "telegram":
        print("Starting Telegram bot only...")
        run_telegram_bot()
    
    elif mode == "both":
        print("Starting both API server and Telegram bot...")
        print("API will be available at http://localhost:8000")
        print("Telegram bot is listening for messages...")
        print("\nPress Ctrl+C to stop.\n")
        
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        api_thread.start()
        
        try:
            run_telegram_bot()
        except KeyboardInterrupt:
            print("\nShutting down Jarvis...")
            sys.exit(0)
    
    else:
        print(f"Unknown mode: {mode}")
        print("Set JARVIS_MODE to 'api', 'telegram', or 'both'")
        sys.exit(1)


if __name__ == "__main__":
    main()
