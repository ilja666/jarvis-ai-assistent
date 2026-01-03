import logging
import sqlite3
import datetime
import os
import subprocess
import pyautogui
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID
def ollama_chat(prompt):
    try:
        # Probeer eerst llama3.2, daarna andere modellen
        models_to_try = ["llama3.2", "qwen2.5", "llama2", "dolphin-mistral"]

        for model in models_to_try:
            try:
                r = requests.post('http://localhost:11434/api/generate',
                                 json={
                                     "model": model,
                                     "prompt": prompt,
                                     "stream": False
                                 }, timeout=15)
                if r.status_code == 200:
                    return r.json()['response']
            except:
                continue  # Probeer volgende model

        return "Geen werkend Ollama model gevonden. Start Ollama en download een model."

    except requests.exceptions.RequestException as e:
        return f"Ollama server niet bereikbaar. Start Ollama eerst: {str(e)}"
    except Exception as e:
        return f"Ollama fout: {str(e)}"

# --- CONFIG ---
TOKEN = TELEGRAM_BOT_TOKEN

# DB setup
db_path = "jarvis_log.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (timestamp TEXT, user TEXT, action TEXT, details TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes (timestamp TEXT, note TEXT)''')
conn.commit()

def log_action(user, action, details=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO logs VALUES (?, ?, ?, ?)", (timestamp, str(user), action, details))
    conn.commit()

def add_note(note):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO notes VALUES (?, ?)", (timestamp, note))
    conn.commit()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTHORIZED_USER_ID
    user_id = update.effective_user.id
    if AUTHORIZED_USER_ID is None:
        AUTHORIZED_USER_ID = user_id
        await update.message.reply_text("Jarvis online 🚀 Jij bent de baas.")
        log_action(user_id, "start", "Authorized")
    elif user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Toegang geweigerd.")
        return
    else:
        await update.message.reply_text("Jarvis klaar voor commando's, baas.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if AUTHORIZED_USER_ID is None or user_id != AUTHORIZED_USER_ID:
        return

    text = update.message.text.lower().strip()
    log_action(user_id, "command", text)

    # === SLIM ANTWOORD MET OLLAMA ===
    if text.startswith("ask "):
        question = text[4:].strip()
        answer = ollama_chat(f"Beantwoord kort en duidelijk in het Nederlands: {question}")
        await update.message.reply_text(answer)
        log_action(user_id, "ollama_ask", question)
        return

    # === BASIS ===
    if text == "status":
        await update.message.reply_text(f"Jarvis draait op {os.uname().nodename if hasattr(os, 'uname') else os.name}\nTijd: {datetime.datetime.now()}")
    
    elif text == "log":
        c.execute("SELECT timestamp, action, details FROM logs ORDER BY timestamp DESC LIMIT 15")
        rows = c.fetchall()
        response = "Laatste acties:\n\n"
        for row in rows:
            response += f"{row[0]} | {row[1]} | {row[2]}\n"
        await update.message.reply_text(response or "Nog geen logs.")

    elif text == "screenshot":
        screenshot_path = "screen.png"
        try:
            pyautogui.screenshot(screenshot_path)
            await update.message.reply_photo(open(screenshot_path, "rb"))
            os.remove(screenshot_path)
            log_action(user_id, "screenshot", "Sent")
        except Exception as e:
            await update.message.reply_text(f"Fout bij maken screenshot: {e}")

    # === APPS OPENEN ===
    elif text.startswith("open "):
        app = text[5:].strip().lower()

        # Windows app mappings
        app_paths = {
            'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
            'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            'notepad': 'notepad.exe',
            'calc': 'calc.exe',
            'explorer': 'explorer.exe',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe',
            'code': 'code.cmd',  # VS Code
            'cursor': r'C:\Users\Ilja\AppData\Local\Programs\cursor\Cursor.exe',
            'word': r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE',
            'excel': r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE',
            'powerpoint': r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE',
        }

        try:
            if os.name == 'nt':  # Windows
                if app in app_paths:
                    subprocess.Popen([app_paths[app]], shell=True)
                    await update.message.reply_text(f"✅ {app} geopend.")
                else:
                    # Probeer als commando in PATH
                    subprocess.Popen(app, shell=True)
                    await update.message.reply_text(f"✅ {app} gestart (als commando).")
            else:  # Linux/Mac
                subprocess.Popen(app.split())
                await update.message.reply_text(f"✅ {app} geopend.")

            log_action(user_id, "open_app", app)

        except FileNotFoundError:
            await update.message.reply_text(f"❌ {app} niet gevonden. Controleer of het geïnstalleerd is.")
        except Exception as e:
            await update.message.reply_text(f"❌ Fout bij openen {app}: {str(e)}")

    # Voorbeelden:
    # open chrome, open notepad, open code, open cursor, open word

    # === NOTITIES ===
    elif text.startswith("note "):
        note = text[5:].strip()
        add_note(note)
        await update.message.reply_text(f"Notitie opgeslagen: {note}")
        log_action(user_id, "note", note)

    elif text == "notes":
        c.execute("SELECT timestamp, note FROM notes ORDER BY timestamp DESC LIMIT 10")
        rows = c.fetchall()
        response = "Laatste notities:\n\n"
        for row in rows:
            response += f"{row[0]} → {row[1]}\n"
        await update.message.reply_text(response or "Geen notities nog.")

    # === CURSOR: NIEUW PROJECT ===
    elif text == "nieuw project" or text == "new project":
        try:
            # Cursor pad voor huidige gebruiker
            cursor_path = r"C:\Users\Ilja\AppData\Local\Programs\cursor\Cursor.exe"

            if os.path.exists(cursor_path):
                subprocess.Popen([cursor_path])
                time.sleep(3)
                # Ctrl+N voor nieuw project
                pyautogui.hotkey('ctrl', 'n')
                time.sleep(1)
                pyautogui.write("nieuw-project-jarvis")
                pyautogui.press('enter')
                await update.message.reply_text("✅ Cursor geopend + nieuw project 'nieuw-project-jarvis' gestart.")
                log_action(user_id, "new_project", "Cursor")
            else:
                await update.message.reply_text("❌ Cursor niet gevonden. Installeer Cursor eerst.")

        except Exception as e:
            await update.message.reply_text(f"❌ Fout bij nieuw project: {str(e)}")

    # === OLLAMA INTEGRATIE KOMT HIERONDER ===

    else:
        await update.message.reply_text(f"Commando '{text}' ontvangen – nog niet gekend, maar gelogd. Zeg 'help' voor opties.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 Jarvis commando's:

📊 BASIS:
- status              → huidige status
- screenshot         → maak screenshot
- log                → laatste acties
- help               → deze lijst

🚀 APPS (Windows):
- open chrome        → Google Chrome
- open firefox       → Firefox browser
- open edge          → Microsoft Edge
- open notepad       → Kladblok
- open calc          → Rekenmachine
- open code          → VS Code
- open cursor        → Cursor editor
- open word          → Microsoft Word
- open excel         → Microsoft Excel
- open cmd           → Command Prompt
- nieuw project      → opent Cursor + nieuw project

📝 NOTITIES:
- note [tekst]       → sla notitie op
- notes              → toon laatste notities

🧠 AI CHAT (vereist Ollama):
- ask [vraag]        → vraag aan AI

Modellen: llama3.2, qwen2.5, llama2, dolphin-mistral
Voorbeeld: ask wat is de hoofdstad van Frankrijk?
    """
    await update.message.reply_text(help_text)

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Jarvis draait – wacht op commando's via Telegram")
    application.run_polling()

if __name__ == '__main__':
    main()