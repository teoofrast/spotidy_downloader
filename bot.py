import asyncio
import logging
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

from downloader import SpotifyDownloaderFacade
from logger_file import setup_logger
from database import initialize_database, create_db_engine
from models import init_db

load_dotenv()
logger = setup_logger(__name__)

TOKEN = getenv("BOT_TOKEN")
RAPID_API_KEY = getenv("RAPID_API_KEY")
CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!. Кидай ссылку на трек в Spotify и будет счастье!")


@dp.message()
async def download_song(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    if message.text.startswith('https://open.spotify.com/track/'):
        logger.info(
            'Пришло сообщение с ссылкой от пользователя с id - %s, с ником - %s, и содержание сообщения - %s',
            message.from_user.id,
            message.from_user.username,
            message.text
        )
        downloader = SpotifyDownloaderFacade(RAPID_API_KEY)
        asyncio.create_task(downloader.get_mp3(message.text, CLIENT_ID, CLIENT_SECRET, bot, message.chat.id))
        await message.answer('Ваша ссылка принята в работу')
    else:
        logger.info(
            'Пришло сообщение без ссылки от пользователя с id - %s, с ником - %s, и содержание сообщения - %s',
            message.from_user.id,
            message.from_user.username,
            message.text
        )
        await message.answer('Неверная ссылка. Перепроверьте и попробуйте ещё раз.')



async def main() -> None:
    await initialize_database()
    engine = await create_db_engine()
    await init_db(engine)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
