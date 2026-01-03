# 🤖 Jarvis AI Assistant

Een persoonlijke AI-assistent zoals Tony Stark's Jarvis, gebouwd met Python en Telegram.

## 🚀 Snel starten

1. **Installeer dependencies:**
   ```bash
   pip install python-telegram-bot psutil pyautogui pillow python-dotenv requests
   ```

2. **Stel je bot token in:**
   - Ga naar Telegram en zoek `@BotFather`
   - Maak een nieuwe bot met `/newbot`
   - Kopieer de token
   - Plak hem in `.env`: `TELEGRAM_BOT_TOKEN=jouw_token_hier`

3. **Start Jarvis:**
   ```bash
   python jarvis_remote2.py
   ```

4. **Activeer in Telegram:**
   - Start een chat met je bot
   - Typ `/start` (jij wordt automatisch eigenaar)
   - Typ `help` voor alle commando's

## 📱 Beschikbare commando's

### Basis commando's
- `status` - Toon huidige status en tijd
- `screenshot` - Maak screenshot van je computer
- `log` - Toon laatste 15 acties
- `help` - Toon deze lijst

### Apps openen (Windows)
- `open chrome` - Google Chrome
- `open firefox` - Firefox browser
- `open edge` - Microsoft Edge
- `open notepad` - Kladblok
- `open calc` - Rekenmachine
- `open code` - VS Code
- `open cursor` - Cursor editor
- `open word` - Microsoft Word
- `open excel` - Microsoft Excel
- `open cmd` - Command Prompt

### Notities systeem
- `note [tekst]` - Sla een notitie op
- `notes` - Toon laatste 10 notities

### AI Chat (vereist Ollama)
- `ask [vraag]` - Stel vraag aan AI

**Beschikbare modellen:** llama3.2, qwen2.5, llama2, dolphin-mistral
Voorbeeld: `ask wat is de hoofdstad van Frankrijk?`

### Geavanceerd
- `nieuw project` - Open Cursor en maak nieuw project

## 🧠 Ollama Setup (voor AI chat)

1. **Installeer Ollama:** https://ollama.ai/
2. **Download model:**
   ```bash
   ollama pull llama3.2
   ```
3. **Start Ollama service:**
   ```bash
   ollama serve
   ```

## 🔧 Configuratie

- `.env` - Bevat je bot token (niet naar Git!)
- `config.py` - Laadt environment variabelen
- `jarvis_log.db` - SQLite database voor logs en notities

## 🛡️ Beveiliging

- Alleen de eerste gebruiker die `/start` typt wordt eigenaar
- Andere gebruikers krijgen "Toegang geweigerd"
- Alle acties worden gelogd in de database

## 📊 Logs bekijken

Typ `log` in je bot om de laatste acties te zien, of bekijk direct in de database:

```bash
sqlite3 jarvis_log.db
.schema
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10;
```

---

**Gemaakt met ❤️ voor AI-liefhebbers**
