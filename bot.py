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

last_messages = {}

async def send_and_store_message(chat_id: int, text: str) -> int:
    """Отправляет сообщение и возвращает его ID."""
    sent_message = await bot.send_message(chat_id, text)
    return sent_message.message_id

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    chat_id = message.chat.id
    user_message_id = message.message_id

    bot_message_id = await send_and_store_message(chat_id, f"Hello, {html.bold(message.from_user.full_name)}!. Кидай ссылку на трек в Spotify и будет счастье!")

    last_messages[chat_id] = {"user": user_message_id, "bot": bot_message_id}
    logger.info(last_messages)

@dp.message(Command('delete'))
async def delete_previous_messages(message: Message):
    chat_id = message.chat.id
    user_command_message_id = message.message_id  # ID сообщения с командой /delete

    deleted_count = 0

    if chat_id in last_messages and 'user' in last_messages[chat_id] and 'bot' in last_messages[chat_id]:
        user_to_delete_id = last_messages[chat_id]['user']
        bot_to_delete_id = last_messages[chat_id]['bot']

        try:
            await bot.delete_message(chat_id, user_to_delete_id)
            print(f"Удалено сообщение пользователя ID {user_to_delete_id} в чате {chat_id}")
            deleted_count += 1
        except Exception as e:
            print(f"Ошибка при удалении сообщения пользователя: {e}")

        try:
            await bot.delete_message(chat_id, bot_to_delete_id)
            logger.info("Удалено сообщение бота ID %s в чате %s", bot_to_delete_id, chat_id)
            deleted_count += 1
        except Exception as e:
            logger.info("Ошибка при удалении сообщения бота: %s", e)

        # Очищаем сохраненные ID
        del last_messages[chat_id]
    else:
        reply_message = await message.reply("Нет предыдущих сообщений для удаления или они не были сохранены.")
        # Сохраняем ID сообщения пользователя с командой /delete и сообщения бота об отсутствии
        last_messages[chat_id] = {"user": user_command_message_id, "bot": reply_message.message_id}

    # Пытаемся удалить сообщение с командой /delete
    try:
        await bot.delete_message(chat_id, user_command_message_id)
        logger.info("Удалено сообщение с командой /delete ID %s в чате %s", user_command_message_id, chat_id)
        deleted_count += 1
    except Exception as e:
        logger.info("Ошибка при удалении сообщения с командой /delete: %s", e)

    if deleted_count == 0 and chat_id not in last_messages:
        reply_message = await message.reply("Нет сообщений для удаления.")
        last_messages[chat_id] = {"user": user_command_message_id, "bot": reply_message.message_id}


@dp.message()
async def download_song(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    chat_id = message.chat.id
    user_message_id = message.message_id

    if message.text.startswith('https://open.spotify.com/track/'):
        logger.info(
            'Пришло сообщение с ссылкой от пользователя с id - %s, с ником - %s, и содержание сообщения - %s',
            message.from_user.id,
            message.from_user.username,
            message.text
        )
        downloader = SpotifyDownloaderFacade(RAPID_API_KEY)
        asyncio.create_task(downloader.get_mp3(message.text, CLIENT_ID, CLIENT_SECRET, bot, chat_id))
        reply_message = await message.answer('Ваша ссылка принята в работу')
        last_messages[chat_id] = {"user": user_message_id, "bot": reply_message.message_id}
    else:
        logger.info(
            'Пришло сообщение без ссылки от пользователя с id - %s, с ником - %s, и содержание сообщения - %s',
            message.from_user.id,
            message.from_user.username,
            message.text
        )
        reply_message = await message.answer('Неверная ссылка. Перепроверьте и попробуйте ещё раз.')
        last_messages[chat_id] = {"user": user_message_id, "bot": reply_message.message_id}



async def main() -> None:
    await initialize_database()
    engine = await create_db_engine()
    await init_db(engine)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
