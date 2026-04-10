import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Configúralo en Railway
ADMINS = [123456789]  # Sustituye por tu ID de Telegram
GROUP_ID = -1001234567890  # ID del grupo
PAYPAL_LINK = "https://paypal.me/bucefalo74"
