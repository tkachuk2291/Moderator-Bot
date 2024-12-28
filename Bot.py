from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, Update
from aiogram.filters import Command
from contextlib import suppress
import logging
import asyncio
from Bot_config import *

# Ініціалізація бота
bot = Bot(BOT_TOKEN)
router = Router()

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Команда для створення репорту --- #
@router.message(Command("report"))
async def report_user(message: Message):
    logger.info(f"Команда /report отримана від {message.from_user.id}")

    if not message.reply_to_message:
        await message.reply("\u274C Ви повинні відповісти на повідомлення користувача, на якого хочете надіслати скаргу.")
        return

    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention_html()
    reporter = message.from_user.mention_html()

    # Відправка скарги в адмінський чат
    try:
        await bot.send_message(
            admin_chat_id,
            f"\u26A0\uFE0F <b>Новий репорт</b>:\n"
            f"\uD83D\uDC64 <b>Користувач:</b> {mention}\n"
            f"\uD83D\uDCDD <b>Репортер:</b> {reporter}\n"
            f"\uD83D\uDCCC <b>Чат:</b> {message.chat.title}\n"
            f"\uD83D\uDD17 <a href='https://t.me/{message.chat.username}/{message.reply_to_message.message_id}'>Посилання на повідомлення</a>",
            parse_mode="HTML"
        )
        await message.reply("\u2705 Репорт успішно надіслано адміністраторам.")
    except Exception as e:
        logger.error(f"Помилка у репорті: {e}")
        await message.reply("\u274C Не вдалося надіслати репорт. Спробуйте ще раз.")

# --- Карма: додавання та перегляд --- #
@router.message(Command("karma"))
async def check_karma(message: Message):
    logger.info(f"Команда /karma отримана від {message.from_user.id}")

    if not message.reply_to_message:
        user_id = message.from_user.id
        mention = message.from_user.mention_html()
    else:
        user_id = message.reply_to_message.from_user.id
        mention = message.reply_to_message.from_user.mention_html()

    karma = user_karma.get(user_id, DEFAULT_USER_KARMA)
    await message.reply(f"\uD83D\uDCDD Карма користувача {mention}: <b>{karma}</b>", parse_mode="HTML")

# Оновлення карми (+<число> або -<число>)
@router.message()
async def update_karma(message: Message):
    if not message.reply_to_message:
        return

    # Перевірка формату (+<число> або -<число>)
    text = message.text.strip()
    if not (text.startswith("+") or text.startswith("-")):
        return

    try:
        karma_change = int(text)
    except ValueError:
        return

    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention_html()

    # Ініціалізація карми, якщо користувача немає в базі
    if user_id not in user_karma:
        user_karma[user_id] = DEFAULT_ADMIN_KARMA if user_id == admin_chat_id else DEFAULT_USER_KARMA

    # Оновлення карми
    user_karma[user_id] += karma_change
    user_karma[user_id] = max(MIN_KARMA, min(MAX_KARMA, user_karma[user_id]))  # Обмеження діапазону

    # Відправлення повідомлення
    await message.reply(
        f"\uD83D\uDCDD Карма користувача {mention} оновлена: {karma_change:+}\n"
        f"\uD83D\uDD22 Нова карма: {user_karma[user_id]}",
        parse_mode="HTML"
    )

# --- Перегляд акаунтів --- #
@router.message(Command("myaccount"))
async def view_account(message: Message):
    logger.info(f"Команда /myaccount отримана від {message.from_user.id}")

    user = message.from_user

    # Інформація про користувача
    account_info = (
        f"\uD83D\uDC64 <b>Ім'я:</b> {user.full_name}\n"
        f"\uD83D\uDD16 <b>ID:</b> {user.id}\n"
        f"\uD83D\uDCCE <b>Посилання:</b> {user.mention_html()}"
    )

    await message.reply(account_info, parse_mode="HTML")

@router.message(Command("useraccount"))
async def admin_view_account(message: Message):
    logger.info(f"Команда /useraccount отримана від {message.from_user.id}")

    if not message.reply_to_message:
        await message.reply("\u274C Ви повинні відповісти на повідомлення користувача, інформацію про якого хочете отримати.")
        return

    user = message.reply_to_message.from_user

    # Інформація для адміністраторів
    account_info = (
        f"\uD83D\uDC64 <b>Ім'я:</b> {user.full_name}\n"
        f"\uD83D\uDD16 <b>ID:</b> {user.id}\n"
        f"\uD83D\uDCCE <b>Посилання:</b> {user.mention_html()}\n"
        f"\uD83D\uDD14 <b>Кількість попереджень:</b> {warnings.get(user.id, 0)}\n"
        f"\uD83D\uDCDD <b>Карма:</b> {user_karma.get(user.id, DEFAULT_USER_KARMA)}"
    )

    await message.reply(account_info, parse_mode="HTML")

# --- Універсальний хендлер для необроблених оновлень --- #
@router.update()
async def log_unhandled_update(update: Update):
    logger.warning(f"Unhandled update: {update}")

# --- Реєстрація хендлерів --- #
dp = Dispatcher()
dp.include_router(router)

# --- Запуск --- #
async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Глобальна помилка: {e}")

if __name__ == "__main__":
    asyncio.run(main())