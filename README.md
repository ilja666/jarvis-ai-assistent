# Jarvis AI Assistant

A modular personal AI assistant inspired by Tony Stark's Jarvis. Control your Windows PC, AI tools (Cursor, Claude, Grok), and Kali VM from your Android phone using natural language.

## Features

- **Natural Language Control**: Just tell Jarvis what you want - no memorizing commands
- **Modular Architecture**: Add/remove application modules as needed
- **Telegram Interface**: Control from your phone via Telegram
- **REST API**: Integrate with other tools via HTTP API
- **AI-Powered**: Uses Ollama for intelligent request interpretation
- **Full GUI Automation**: Screenshots, window control, keyboard/mouse
- **Kali VM Integration**: SSH-based control of your Kali Linux VM
- **Cursor IDE Control**: Project management, file creation, git operations
- **Audit Logging**: All actions logged for security and debugging

## Quick Start (New Modular Version)

### Prerequisites

- Python 3.10+
- Windows 11 (for GUI automation)
- Ollama installed and running
- Telegram Bot Token (from @BotFather)
- Tailscale (for remote access from phone)

### Installation

```bash
cd home_agent
pip install poetry
poetry install
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your settings:
# - TELEGRAM_BOT_TOKEN (required)
# - KALI_HOST, KALI_PASSWORD (optional, for Kali VM)
```

### Running Jarvis

```bash
cd home_agent
poetry run python run_agent.py
```

This starts both the API server (port 8000) and Telegram bot.

To run only one component:
```bash
# API only
JARVIS_MODE=api poetry run python run_agent.py

# Telegram only
JARVIS_MODE=telegram poetry run python run_agent.py
```

## Usage

### Telegram (Natural Language)

Just message your bot naturally:

- "Take a screenshot"
- "Open Chrome"
- "What's the system status?"
- "Create a new Python project called myapp"
- "Check if Kali is connected"
- "Save a note: remember to update the docs"

### API Endpoints

```bash
# Send natural language message
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"message": "take a screenshot"}'

# Execute specific action
curl -X POST http://localhost:8000/action \
  -H "Content-Type: application/json" \
  -d '{"capability": "system.screenshot", "params": {}}'

# List all modules
curl http://localhost:8000/modules

# List all capabilities
curl http://localhost:8000/capabilities
```

## Modules

| Module | Description | Key Capabilities |
|--------|-------------|------------------|
| system | Screenshots, status, notes | screenshot, status, add_note, list_windows |
| windows | App control, keyboard/mouse | open_app, close_app, type_text, press_key |
| cursor | Cursor IDE integration | open, create_project, git_status, git_commit |
| kali | Kali VM via SSH | run_command, check_connection, list_tools |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Telegram Bot   │     │   REST API      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │     AI      │
              │ Interpreter │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  Dispatcher │
              └──────┬──────┘
                     │
    ┌────────┬───────┼───────┬────────┐
    │        │       │       │        │
┌───▼──┐ ┌───▼──┐ ┌──▼──┐ ┌──▼──┐ ┌───▼───┐
│System│ │Windows│ │Cursor│ │Kali│ │ More  │
│Module│ │Module │ │Module│ │SSH │ │Modules│
└──────┘ └───────┘ └──────┘ └────┘ └───────┘
```

## Remote Access with Tailscale

1. Install Tailscale on your Windows PC and Android phone
2. Login to the same Tailscale account on both
3. Your PC gets an IP like `100.x.x.x`
4. Access the API from your phone: `http://100.x.x.x:8000`

## Kali VM Setup

1. In your Kali VM, enable SSH:
   ```bash
   sudo systemctl start ssh
   sudo systemctl enable ssh
   ip a  # Note the IP address
   ```

2. Add to your `.env`:
   ```
   KALI_HOST=192.168.x.x
   KALI_USER=kali
   KALI_PASSWORD=your_password
   ```

## Security

- First Telegram user to `/start` becomes the owner
- All actions are logged with timestamps
- Dangerous actions require confirmation
- Kali commands require explicit confirmation

## Legacy Version

The original command-based bot is still available in `jarvis_remote2.py` if you prefer predetermined commands over natural language.

## Tech Stack

- **FastAPI** - REST API server
- **python-telegram-bot** - Telegram integration
- **Ollama** - Local AI for natural language understanding
- **pyautogui/pywinauto** - GUI automation
- **paramiko** - SSH for Kali VM
- **SQLite** - Audit logging and notes

## License

MIT
