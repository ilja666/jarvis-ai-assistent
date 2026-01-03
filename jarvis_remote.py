import logging
import sqlite3
import datetime
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID

# --- CONFIG ---
TOKEN = TELEGRAM_BOT_TOKEN

# Setup logging naar DB
db_path = "jarvis_log.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (timestamp TEXT, user TEXT, action TEXT, details TEXT)''')
conn.commit()

def log_action(user, action, details=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO logs VALUES (?, ?, ?, ?)", (timestamp, str(user), action, details))
    conn.commit()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTHORIZED_USER_ID
    user_id = update.effective_user.id
    if AUTHORIZED_USER_ID is None:
        AUTHORIZED_USER_ID = user_id
        await update.message.reply_text("Jarvis online 🚀\nJij bent nu de baas. Anderen worden geblokkeerd.")
        log_action(user_id, "start", "Authorized user set")
    elif user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Toegang geweigerd.")
        return
    else:
        await update.message.reply_text("Jarvis staat klaar, baas.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if AUTHORIZED_USER_ID is None or user_id != AUTHORIZED_USER_ID:
        return
    
    text = update.message.text
    log_action(user_id, "command", text)
    
    if text.lower() == "status":
        await update.message.reply_text(f"Jarvis draait sinds {datetime.datetime.now()}\nAlles goed hier.")
    elif text.lower() == "log":
        c.execute("SELECT timestamp, action, details FROM logs ORDER BY timestamp DESC LIMIT 10")
        rows = c.fetchall()
        response = "Laatste 10 acties:\n\n"
        for row in rows:
            response += f"{row[0]} | {row[1]} | {row[2]}\n"
        await update.message.reply_text(response)
    elif text.lower() == "screenshot":
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save("temp_screen.png")
        await update.message.reply_photo(open("temp_screen.png", "rb"))
        os.remove("temp_screen.png")
        log_action(user_id, "screenshot", "Sent")
    else:
        await update.message.reply_text(f"Commando ontvangen: {text}\nNog niet geïmplementeerd, maar gelogd 😉")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Jarvis draait... wacht op commando's")
    application.run_polling()

if __name__ == '__main__':
    main()