import asyncio
import logging
import psutil
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

from downloader import SpotifyDownloaderFacade
from logger_file import setup_logger

load_dotenv()
logger = setup_logger(__name__)

TOKEN = getenv("BOT_TOKEN")
RAPID_API_KEY = getenv("RAPID_API_KEY")
CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

def get_process_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    return memory_info.rss / (1024 * 1024)  # в MB

async def clear_chat(chat_id: int):
    """Удаляет все сообщения в чате, кроме отправленных файлов."""
    try:
        offset = 0
        while True:
            updates = await bot.get_updates(offset=offset, limit=100)
            if not updates:
                break
            for update in updates:
                if update.message and update.message.chat.id == chat_id:
                    if not update.message.audio:
                        await bot.delete_message(chat_id, update.message.message_id)
                    offset = update.update_id + 1
    except Exception as e:
        logging.error(f"Ошибка при очистке чата: {e}")

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!. Кидай ссылку на трек в Spotify и будет счастье!")


@dp.message(Command("clear"))
async def handle_clear_command(message: Message):
        await clear_chat(message.chat.id)
        await message.answer("Чат очищен.")

@dp.message()
async def download_song(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    if message.text.startswith('https://open.spotify.com/track/'):
        downloader = SpotifyDownloaderFacade(RAPID_API_KEY)
        asyncio.create_task(downloader.get_mp3(message.text, CLIENT_ID, CLIENT_SECRET, bot, message.chat.id))
        await message.answer('Мы приняла Вашу ссылку в работу')
        logger.info(f"Memory usage after download task: {get_process_memory():.2f} MB")
    else:
        await message.answer('Э скинь норм ссылку. Чо творишь то?')



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
