import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
DATABASE_TYPE = os.getenv('DATABASE_TYPE')
SQLITE_FILENAME = os.getenv('SQLITE_FILENAME')