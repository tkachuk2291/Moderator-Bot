from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command
from datetime import datetime, timedelta
from contextlib import suppress
import asyncio
import logging
from Bot_config import warnings, admin_chat_id, BOT_TOKEN

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)

# Ініціалізація бота та маршрутизатора
bot = Bot(BOT_TOKEN)
router = Router()

# Функція розбору часу
def parse_time(time_str: str) -> int:
    time_mapping = {"m": 1, "h": 60, "d": 1440, "w": 10080}
    try:
        unit = time_str[-1]
        amount = int(time_str[:-1])
        return amount * time_mapping.get(unit, 0)
    except (ValueError, IndexError):
        return None

# Форматування часу
def format_time(minutes: int) -> str:
    target_time = datetime.now() + timedelta(minutes=minutes)
    return target_time.strftime("%d-%m-%Y %H:%M")

# Завантаження списку заборонених слів
mate_words = []
try:
    with open('mate.txt', 'r', encoding='utf-8') as input_file:
        for line in input_file:
            word = line.strip()
            if word:
                mate_words.append(word)
except FileNotFoundError:
    logging.error("Файл 'mate.txt' не знайдено. Перевірте його наявність.")

# Хендлер для перевірки заборонених слів
@router.message(F.text)
async def check_mate_words(message: Message):
    text = message.text.lower()
    for word in mate_words:
        if word in text:
            await message.delete()
            await message.reply("❌ Ви використали недопустиме слово!")
            return

# Команда /mute
@router.message(Command(commands=["mute"]))
async def mute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❌ Ви повинні відповісти на повідомлення користувача, якого хочете зам'ютити.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Вкажіть час, наприклад: `/mute 10m` або `/mute 1h`.")
        return

    mute_duration = parse_time(args[1])
    if mute_duration is None:
        await message.reply("❌ Неправильний формат часу! Використовуйте: `/mute 10m`, `/mute 1h`, тощо.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    mention = message.reply_to_message.from_user.mention_html()

    warnings[user_id] = warnings.get(user_id, 0) + 1
    current_warnings = warnings[user_id]

    target_datetime = datetime.now() + timedelta(minutes=mute_duration)
    target_time = format_time(mute_duration)

    try:
        with suppress(Exception):
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(),
                until_date=target_datetime.timestamp(),
            )
            await message.reply(
                f"🔇 Користувача {mention} було зам'ютжено до {target_time}. "
                f"<b>Попередження: {current_warnings}/3.</b>",
                parse_mode="HTML"
            )

        if current_warnings >= 3:
            await bot.send_message(
                admin_chat_id,
                f"⚠️ Користувач {mention} має {current_warnings} попередження! Рекомендуємо розглянути бан.",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply(f"❌ Помилка: {e}")

# Команда /unmute
@router.message(Command(commands=["unmute"]))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❌ Ви повинні відповісти на повідомлення користувача, якого хочете розм'ючити.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    mention = message.reply_to_message.from_user.mention_html()

    warnings.pop(user_id, None)

    try:
        with suppress(Exception):
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await message.reply(
                f"✅ Користувача {mention} було розм'ючено. Попередження скинуті.",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply(f"❌ Помилка: {e}")

# Команда /myaccount
@router.message(Command(commands=["myaccount"]))
async def my_account(message: Message):
    user = message.from_user
    full_name = user.full_name
    user_id = user.id

    member = await bot.get_chat_member(message.chat.id, user_id)
    status = "Адмін" if member.status in ["administrator", "creator"] else "Підписник"

    response = (
        f"👤 <b>Ім'я:</b> {full_name}\n"
        f"🆔 <b>Мій ID:</b> {user_id}\n"
        f"⚡ <b>Статус:</b> {status}"
    )

    await message.reply(response, parse_mode="HTML")

# Команда /report
@router.message(Command(commands=["report"]))
async def report_message(message: Message):
    if message.reply_to_message:
        reported_user = message.reply_to_message.from_user
        reported_text = message.reply_to_message.text
        reporter = message.from_user

        admin_message = (
            f"⚠️ <b>Новий репорт!</b>\n"
            f"👤 <b>Користувач:</b> {reported_user.full_name} (ID: {reported_user.id})\n"
            f"📝 <b>Текст:</b> {reported_text}\n"
            f"📣 <b>Відправник репорту:</b> {reporter.full_name} (ID: {reporter.id})"
        )

        await bot.send_message(admin_chat_id, admin_message, parse_mode="HTML")
        await message.reply("✅ Ви відправили репорт, чекайте відповідь Адміністратора!")
    else:
        await message.reply("❌ Репорт може бути відправлений лише як відповідь на повідомлення.")

# Реєстрація хендлерів
dp = Dispatcher()
dp.include_router(router)

# Запуск
async def main():
    logging.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Помилка запуску бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())