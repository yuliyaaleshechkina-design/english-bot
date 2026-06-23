import os

# Ключи берутся из переменных окружения Railway
# На Railway добавь их в Settings -> Variables
BOT_TOKEN    = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DB_PATH      = "bot_database.db"
