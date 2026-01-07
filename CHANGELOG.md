# CHANGELOG

Jarvis AI Assistant - Version History

---

## Devin AI - 2026-01-07 19:08

- Added modular plugin architecture with AI-driven natural language control
- Created Home Agent FastAPI server with REST API endpoints
- Implemented AI interpreter using Ollama for natural language understanding
- Created System module with screenshot, status, and note capabilities
- Created Windows module for app control and GUI automation
- Created Cursor module for IDE integration
- Created Kali module for SSH access to Kali Linux VM
- Added audit logging to SQLite database
- Added confirmation system for dangerous actions
- Integrated Telegram bot with new modular architecture
- Added .env.example configuration template
- Updated README with setup instructions

************************
NOTE: Initial release of modular architecture. Replaces command-based system with pure natural language interpretation.
************************

---

## Devin AI - 2026-01-07 19:08

- Fixed confirmation flow bug (double confirmation loop)
- Added capability format validation to fix "windows" vs "windows.open_app" errors
- Improved AI prompt to prevent context drift (only act on latest message)
- Added more apps: Android Studio, Claude Desktop, Telegram, Discord, Spotify, Slack, Teams, VirtualBox

************************
NOTE: Bug fixes based on initial user testing. App paths may need adjustment for specific installations.
************************
