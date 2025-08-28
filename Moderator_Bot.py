import logging
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from Bot_config import *

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Завантаження або створення файлу з даними
try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"muted_users": {}, "warnings": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Пошук користувача (reply, @, ID)
async def resolve_user(message: Message, args):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(args) < 2:
        return None
    target = args[-1]
    if target.startswith("@"):  # @username
        try:
            user = await bot.get_chat(target)
            return user
        except:
            return None
    elif target.isdigit():
        try:
            user = await bot.get_chat(int(target))
            return user
        except:
            return None
    return None

# /mute <час> <причина> [@username|id|reply]
@dp.message(Command("mute"))
async def mute_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        reason = " ".join(args[2:]) if len(args) >= 3 else "Без причини"
        target_user = message.reply_to_message.from_user
    else:
        if len(args) < 4:
            await message.reply("<b>❗ Формат: /mute 3h Спам @user або ID або reply</b>")
            return
        reason = " ".join(args[2:-1])
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return

    duration_str = args[1]
    time_multiplier = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}

    try:
        unit = duration_str[-1]
        value = int(duration_str[:-1])
        if unit not in time_multiplier:
            raise ValueError

        delta = timedelta(**{time_multiplier[unit]: value})

        user_id = str(target_user.id)
        user_name = target_user.full_name
        admin_name = message.from_user.full_name

        mute_end_time = datetime.now() + delta
        data["muted_users"][user_id] = mute_end_time.isoformat()
        save_data(data)

        await message.answer(
            f"<b>🔇 Адміністратор {admin_name} заглушив користувача {user_name}</b>\n"
            f"<b>⏰ До {mute_end_time.strftime('%d.%m.%Y %H:%M')}</b>\n"
            f"<b>📌 Причина:</b> {reason}"
        )

    except ValueError:
        await message.reply("<b>❗ Формат часу: 2h, 30m, 1d, 1w</b>")

# /unmute [@username|id|reply]
@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        if len(args) < 2:
            await message.reply("<b>❗ Формат: /unmute @user або ID або reply</b>")
            return
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return

    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_name = message.from_user.full_name

    if user_id in data["muted_users"]:
        del data["muted_users"][user_id]
        save_data(data)
        await message.answer(f"<b>✅ Адміністратор {admin_name} зняв мут з користувача {user_name}</b>")
    else:
        await message.reply("<b>❗ Цей користувач не заглушений.</b>")

# /warn <причина> [@username|id|reply]
@dp.message(Command("warn"))
async def warn_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        reason = " ".join(args[1:]) if len(args) >= 2 else "Без причини"
        target_user = message.reply_to_message.from_user
    else:
        if len(args) < 3:
            await message.reply("<b>❗ Формат: /warn Причина @user або ID або reply</b>")
            return
        reason = " ".join(args[1:-1])
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return

    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_name = message.from_user.full_name

    current_warnings = data["warnings"].get(user_id, 0) + 1
    data["warnings"][user_id] = current_warnings
    save_data(data)

    await message.answer(
        f"<b>⚠️ Адміністратор {admin_name} видав попередження користувачу {user_name}</b>\n"
        f"<b>📌 Причина:</b> {reason}\n"
        f"<b>🚧 Попереджень: {current_warnings}/3</b>"
    )

# /ban <час> <причина> [@username|id|reply]
@dp.message(Command("ban"))
async def ban_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        reason = " ".join(args[2:]) if len(args) >= 3 else "Без причини"
        target_user = message.reply_to_message.from_user
    else:
        if len(args) < 4:
            await message.reply("<b>❗ Формат: /ban 3d Образа @user або ID або reply</b>")
            return
        reason = " ".join(args[2:-1])
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return

    duration_str = args[1]
    time_multiplier = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}

    try:
        unit = duration_str[-1]
        value = int(duration_str[:-1])
        if unit not in time_multiplier:
            raise ValueError

        delta = timedelta(**{time_multiplier[unit]: value})
        ban_end_time = datetime.now() + delta

        user_id = str(target_user.id)
        user_name = target_user.full_name
        admin_name = message.from_user.full_name

        data["banned_users"][user_id] = ban_end_time.isoformat()
        save_data(data)

        # Запис в історію
        entry = {
            "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "admin": admin_name,
            "user": user_name,
            "user_id": user_id,
            "action": "ban",
            "reason": reason
        }
        data["history"].append(entry)
        save_data(data)

        await message.answer(
            f"<b>🔒 Адміністратор {admin_name} забанив {user_name}</b>\n"
            f"<b>⏰ До {ban_end_time.strftime('%d.%m.%Y %H:%M')}</b>\n"
            f"<b>📌 Причина:</b> {reason}"
        )

    except ValueError:
        await message.reply("<b>❗ Формат часу: 2h, 30m, 1d, 1w</b>")
        
@dp.message(Command("history"))
async def history_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(args) >= 2:
        target_user = await resolve_user(message, args)
    else:
        await message.reply("<b>❗ Використання: /history @user або ID або reply</b>")
        return

    user_id = str(target_user.id)
    user_name = target_user.full_name

    history = data.get("history", {}).get(user_id, [])

    if not history:
        await message.reply(f"<b>📜 У користувача {user_name} ще немає покарань.</b>")
        return

    text = [f"<b>📜 Історія покарань {user_name}:</b>"]
    for entry in history:
        if entry["type"] == "warn":
            text.append(f"⚠️ Попередження — {entry['reason']} ({entry['date']})")
        elif entry["type"] == "mute":
            text.append(f"🔇 Мут до {entry['until']} — {entry['reason']} ({entry['date']})")
        elif entry["type"] == "ban":
            text.append(f"🔒 Бан до {entry['until']} — {entry['reason']} ({entry['date']})")

    await message.reply("\n".join(text))

# /unbun [@username|id|reply]
@dp.message(Command("unbun"))
async def unbun_user(message: Message):
    args = message.text.split()
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        if len(args) < 2:
            await message.reply("<b>❗ Формат: /unbun @user або ID або reply</b>")
            return
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return

    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_name = message.from_user.full_name

    if user_id in data["muted_users"]:
        del data["muted_users"][user_id]
    if user_id in data["warnings"]:
        del data["warnings"][user_id]

    save_data(data)

    await message.answer(
        f"<b>✅ Адміністратор {admin_name} зняв довічну заборону з користувача {user_name}</b>"
    )

# /report <причина> (reply або просто)
@dp.message(Command("report"))
async def report_user(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("<b>❗ Вкажіть причину: /report <причина></b>")
        return

    reporter = message.from_user
    reason = " ".join(args[1:])
    reported_user = message.reply_to_message.from_user if message.reply_to_message else None

    reporter_name = reporter.full_name
    reporter_id = reporter.id

    if reported_user:
        reported_name = reported_user.full_name
        reported_id = reported_user.id
    else:
        reported_name = "❓ Невідомо (без reply)"
        reported_id = "—"

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    report_msg = (
        f"🚨 **Новий репорт!**\n"
        f"👤 Від: {reporter_name} (`{reporter_id}`)\n"
        f"🎯 На: {reported_name} (`{reported_id}`)\n"
        f"🕒 Час: {now}\n"
        f"📌 Причина: {reason}"
    )

    async with aiohttp.ClientSession() as session:
        await session.post(DISCORD_WEBHOOK_URL, json={"content": report_msg})

    await message.reply("<b>✅ Ви відправили репорт Очікуйте, на відповідь Адміністратора. Приємного спілкування </b>")

# Автозняття мута
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

# Запуск
async def main():
    asyncio.create_task(check_unmute())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())