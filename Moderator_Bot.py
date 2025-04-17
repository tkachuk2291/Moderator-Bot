import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from datetime import datetime, timedelta
import json
import asyncio
from Bot_config import *

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота і диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Завантаження або створення файлу даних
try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"muted_users": {}, "warnings": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Команда /mute
@dp.message(Command("mute"))
async def mute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("<b>❗ Команда має бути відповіддю на повідомлення!</b>")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("<b>❗ Вкажи час, наприклад: /mute 3h</b>")
        return

    duration_str = args[1]
    time_multiplier = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}

    try:
        unit = duration_str[-1]
        value = int(duration_str[:-1])
        if unit not in time_multiplier:
            raise ValueError

        delta = timedelta(**{time_multiplier[unit]: value})

        user_id = str(message.reply_to_message.from_user.id)
        user_name = message.reply_to_message.from_user.full_name
        admin_name = message.from_user.full_name

        mute_end_time = datetime.now() + delta
        data["muted_users"][user_id] = mute_end_time.isoformat()

        current_warnings = data["warnings"].get(user_id, 0) + 1
        data["warnings"][user_id] = current_warnings

        save_data(data)

        text = (
            f"<b>Адміністратор {admin_name} заглушив користувача {user_name}</b>\n"
            f"<b>До {mute_end_time.strftime('%d.%m.%Y %H:%M')} ({current_warnings}/3 попереджень)</b>"
        )

        await message.answer(text)

        if current_warnings >= 3:
            await ban_user_internal(message, message.reply_to_message.from_user)

    except ValueError:
        await message.reply("<b>❗ Невірний формат часу. Використовуй m, h, d, w (наприклад: 2h, 1d).</b>")

# Команда /unmute
@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("<b>❗ Команда має бути відповіддю на повідомлення!</b>")
        return

    user_id = str(message.reply_to_message.from_user.id)
    user_name = message.reply_to_message.from_user.full_name
    admin_name = message.from_user.full_name

    if user_id in data["muted_users"]:
        del data["muted_users"][user_id]
        save_data(data)
        await message.answer(f"<b>Адміністратор {admin_name} зняв мут з користувача {user_name}</b>")
    else:
        await message.reply("<b>❗ Цей користувач не заглушений.</b>")

# Автоматичне зняття мута
async def check_unmute():
    while True:
        now = datetime.now()
        to_unmute = []
        for user_id, mute_end in data["muted_users"].items():
            if datetime.fromisoformat(mute_end) <= now:
                to_unmute.append(user_id)

        for user_id in to_unmute:
            del data["muted_users"][user_id]
            save_data(data)
        await asyncio.sleep(30)

# Бан якщо 3/3 попереджень
async def ban_user_internal(message, user):
    user_id = str(user.id)
    user_name = user.full_name
    admin_name = message.from_user.full_name

    if user_id in data["muted_users"]:
        del data["muted_users"][user_id]
    if user_id in data["warnings"]:
        del data["warnings"][user_id]

    save_data(data)

    await message.answer(
        f"<b>Адміністратор {admin_name} забанив користувача {user_name} за 3/3 попереджень.</b>"
    )

# Запуск бота
async def main():
    asyncio.create_task(check_unmute())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())