import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'JOUW_TELEGRAM_BOT_TOKEN_HIER')
AUTHORIZED_USER_ID = None  # Wordt automatisch ingesteld bij eerste /start
