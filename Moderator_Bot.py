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
from aiogram.types import ChatPermissions
from  aiogram.filters.command import CommandObject
from datetime import datetime, time
from aiogram import types

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Bot_config import *
from Filters import *
import random
import pandas as pd
from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramBadRequest
import os

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

@dp.message(AntiMat())
async def catch_mat(message: Message):
    await message.delete()

    warn_text = (
        f"🚫 <b>{message.from_user.full_name}</b>, "
        "ваше повідомлення містило ненормативну лексику і було видалено."
    )
    await message.answer(warn_text)

@dp.message(AntiBegger())
async def block_begging(message: Message):
    # спочатку видаляємо
    await message.delete()


@dp.message(Command("replyreport"), IsAdmin())
async def reply_report(message: types.Message):

    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"
    # Список можливих варіантів першої відповіді
    phrases = [
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b>\n\nВітаю, {admin_name} Мчить вам на допомогу.",
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b> {admin_name} вже в дорозі!",
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b>\n\n{admin_name} поспішає вам на допомогу!"
    ]

    # Вибір випадкової фрази
    first_text = random.choice(phrases)
    await message.answer(first_text, parse_mode="HTML")

    # Затримка 3–7 секунд
    await asyncio.sleep(random.randint(3, 7))

    # Друге повідомлення
    second_text = (
        f"💬 <b>Відповідь від {admin_fullname}</b>\n\n"
        f"Вітаю, мене звати {admin_name}, працюю по вашій Заявці."
    )
    await message.answer(second_text, parse_mode="HTML")


def parse_args(text: str):
    """
    Парсить аргументи у форматі:
    <час з суфіксом (m/h/d) або 'перманентний'>, <причина>
    або просто <причина> (для warn)
    """
    if not text:
        return None, "Без причини"

    parts = text.split(",", 1)
    time_part = parts[0].strip().lower()
    reason = parts[1].strip() if len(parts) > 1 else None

    # якщо є тільки причина (наприклад warn матюки)
    if reason is None and not re.match(r"^\d+[mhd]$|^перманентний$", time_part):
        return None, time_part

    if time_part == "перманентний":
        return 0, reason or "Без причини"

    # парсимо число + суфікс
    match = re.match(r"^(\d+)([mhd])$", time_part)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        minutes = 0
        if unit == "m":
            minutes = value
        elif unit == "d":
            minutes = value * 60 * 24
        return minutes, reason or "Без причини"

    # якщо нічого не підійшло → все вважаємо причиною
    return None, text.strip()

def parse_duration(duration_str: str):
    """
    Парсер строк типу '120m', '2h', '3d', 'перманентний'
    Повертає datetime або None (якщо перманентний)
    """
    duration_str = duration_str.strip().lower()

    if duration_str in ["перманентний", "permanent", "perm"]:
        return None  # без обмеження

    unit = duration_str[-1]   # остання буква (m/h/d)
    try:
        value = int(duration_str[:-1])
    except ValueError:
        raise ValueError("❗ Невірний формат часу. Використовуйте наприклад: 30m, 2h, 7d, перманентний")

    if unit == "m":  # хвилини
        return datetime.now() + timedelta(minutes=value)
    elif unit == "h":  # години
        return datetime.now() + timedelta(hours=value)
    elif unit == "d":  # дні
        return datetime.now() + timedelta(days=value)
    else:
        raise ValueError("❗ Невірна одиниця часу. Використовуйте m (хвилини), h (години), d (дні).")
\
    # =================== КАРМА ===================
# Структура: data["karma"] = {user_id: число}
if "karma" not in data:
    data["karma"] = {}

# Встановити карму по дефолту
def get_user_karma(user_id: int, is_admin: bool = False) -> int:
    if str(user_id) not in data["karma"]:
        data["karma"][str(user_id)] = 1000 if is_admin else 0
        save_data(data)
    return data["karma"][str(user_id)]

# Обробка повідомлень з кармою
@dp.message()
async def handle_karma(message: Message):
    if not message.reply_to_message:
        return  # працює тільки у відповідь на повідомлення

    target_user = message.reply_to_message.from_user
    user_id = str(target_user.id)

    text = message.text.strip()

    # Позитивна карма → можна писати "50" або "+50"
    if text.isdigit() or (text.startswith("+") and text[1:].isdigit()):
        value = int(text.replace("+", ""))
        new_karma = min(1000, get_user_karma(target_user.id) + value)

    # Негативна карма → тільки з "-"
    elif text.startswith("-") and text[1:].isdigit():
        value = int(text)
        new_karma = max(-1000, get_user_karma(target_user.id) + value)

    else:
        return  # не підходить під формат

    # Записуємо
    data["karma"][user_id] = new_karma
    save_data(data)

    # Відповідь
    await message.reply(
        f"⚖️ Карма користувача {target_user.full_name}: <b>{new_karma}</b>\n"
        f"(Максимум: 1000 | Мінімум: -1000)"
    )
    
# ---------------- UNBAN ----------------
@dp.message(Command("unban"))
async def unban_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    
    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"
    
    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            only_if_banned=True  # ✅ не буде кікати, якщо юзер не в бані
        )
        
        await message.answer(f"✅ {role} {admin_fullname} Розблокував користувача {target_user.full_name}")
    except Exception as e:
        await message.answer(f"❌ Помилка при розбані: {e}")

# ================= ВСПОМОГАТЕЛЬНА ФУНКЦІЯ =================
def parse_duration(duration_str: str):
    duration_str = duration_str.lower()
    if duration_str == "перманентний":
        return None, "назавжди"

    try:
        num = int("".join(filter(str.isdigit, duration_str)))
    except ValueError:
        return None, None

    if "m" in duration_str:
        return num * 60, f"{num} хвилин"
    elif "h" in duration_str:
        return num * 3600, f"{num} годин"
    elif "d" in duration_str:
        return num * 86400, f"{num} днів"
    return None, None

# ================= BAN =================
@dp.message(Command("ban"))
async def ban_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("❗ Використай: /ban <час або перманентний>, причина (у відповідь на повідомлення)")
        return

    args = command.args
    if not args:
        await message.reply("❗ Формат: /ban <час або перманентний>, причина")
        return

    parts = args.split(",", 1)
    duration_reason = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else "Не вказано"

    target_user = message.reply_to_message.from_user
    seconds, duration_text = parse_duration(duration_reason)


    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"

    try:
        # Якщо перманентний бан
        if seconds is None:
            until_date = None  # немає дати завершення
        else:
            until_date = datetime.now() + timedelta(seconds=seconds)

        # Обмеження повідомлень
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            ),
            until_date=until_date
        )

        await message.answer(
            f"⛔ {role} {admin_fullname} заблокував користувача {target_user.full_name} "
            f"{duration_text if duration_text else 'назавжди'}.\n📋 Причина: {reason}"
        )
    except Exception as e:
        await message.reply(f"❌ Помилка при бані: {e}")

# ================= MUTE =================
@dp.message(Command("mute"))
async def mute_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("❗ Використай: /mute <час>, причина (у відповідь на повідомлення)")
        return

    args = command.args
    if not args:
        await message.reply("❗ Формат: /mute <час>, причина")
        return

    parts = args.split(",", 1)
    duration_reason = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else "Не вказано"

    target_user = message.reply_to_message.from_user
    seconds, duration_text = parse_duration(duration_reason)

    if not seconds:
        await message.reply("❗ Невірний формат часу. Використай: 10m, 2h, 7d")
        return

    until_date = datetime.now() + timedelta(seconds=seconds)


    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"


    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(
            f"🔇 {role} {admin_fullname} видав мут"
            f"користувачу {target_user.full_name} на {duration_text}.\n📋 Причина: {reason}"
        )
    except Exception as e:
        await message.reply(f"❌ Помилка при муті: {e}")


# ---------------- UNMUTE ----------------
@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user


    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.answer(f"🔊 {role} {admin_fullname} зняв мут Користувачу {target_user.full_name}.")
    except Exception as e:
        await message.answer(f"❌ Помилка при знятті мута: {e}")
 
# ====================== /userinfo ======================
@dp.message(Command("userinfo"), IsAdmin())
async def history_user(message: Message):
    args = message.text.split()

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(args) >= 2:
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("❗ Не вдалося знайти користувача.")
            return
    else:
        await message.reply("<b>❗ Використання: /userinfo @user або ID або reply</b>")
        return

    user_id = str(target_user.id)
    user_name = target_user.full_name

    history = data.get("history", {}).get(user_id, [])

    if not history:
        await message.reply(f"<b>📜 У користувача {user_name} ще немає покарань.</b>")
        return

    text = [f"<b>📜 Історія покарань {user_name}:</b>"]
    for i, entry in enumerate(history, start=1):
        if entry["type"] == "warn":
            text.append(f"{i}. ⚠️ Попередження — {entry['reason']} ({entry['date']})")
        elif entry["type"] == "mute":
            text.append(f"{i}. 🔇 Мут до {entry['until']} — {entry['reason']} ({entry['date']})")
        elif entry["type"] == "ban":
            text.append(f"{i}. 🔒 Бан до {entry['until']} — {entry['reason']} ({entry['date']})")
        elif entry["type"] == "kick":
            text.append(f"{i}. 👢 Кік — {entry['reason']} ({entry['date']})")

    await message.reply("\n".join(text))


# ====================== /kick ======================
@dp.message(Command("kick"), IsAdmin())
async def kick_user(message: Message):
    args = message.text.split()

    if message.reply_to_message:
        reason = " ".join(args[1:]) if len(args) > 1 else "Без причини"
        target_user = message.reply_to_message.from_user
    else:
        if len(args) < 3:
            await message.reply("<b>❗ Формат: /kick Причина @user або ID або reply</b>")
            return
        reason = " ".join(args[1:-1])
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return

    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_fullname = message.from_user.full_name
    role = "Адміністратор"

    try:
        # бан на 30 сек + розбан = кік
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id, until_date=datetime.now() + timedelta(seconds=30))
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)

        # Лог історії
        if "history" not in data:
            data["history"] = {}
        if user_id not in data["history"]:
            data["history"][user_id] = []

        data["history"][user_id].append({
            "type": "kick",
            "reason": reason,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        save_data(data)

        await message.answer(
            f"<b>👢 {role} {admin_fullname} Від’єднав користувача {user_name}</b>\n"
            f"<b>📌 Причина:</b> {reason}"
        )

    except Exception as e:
        await message.reply(f"<b>❗ Помилка при виконанні кіку: {e}</b>")


# ====================== /warn ======================
@dp.message(Command("warn"), IsAdmin())
async def warn_user(message: Message, command: Command):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    reason = command.args if command.args else "Без причини"

    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_fullname = message.from_user.full_name
    role = "Адміністратор"

    # Логування в базу
    if "history" not in data:
        data["history"] = {}
    if user_id not in data["history"]:
        data["history"][user_id] = []

    data["history"][user_id].append({
        "type": "warn",
        "reason": reason,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    save_data(data)

    await message.answer(
        f"⚠️ {role} {admin_fullname} Попередив користувача {target_user.full_name}.\n"
        f"📝 Причина: {reason}"
    )


# ====================== /unwarn ======================

@dp.message(Command("unwarn"), IsAdmin())
async def unwarn_user(message: Message):
    args = message.text.split()

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(args) >= 2:
        target_user = await resolve_user(message, args)
        if not target_user:
            await message.reply("<b>❗ Не вдалося знайти користувача.</b>")
            return
    else:
        await message.reply("<b>❗ Формат: /unwarn @user або ID або reply</b>")
        return

    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_fullname = message.from_user.full_name

    history = data.get("history", {}).get(user_id, [])
    if not history:
        await message.reply(f"<b>❗ У користувача {user_name} немає попереджень.</b>")
        return


    user_id = str(target_user.id)
    user_name = target_user.full_name
    admin_fullname = message.from_user.full_name
    role = "Адміністратор"

    # шукаємо останнє попередження
    for i in range(len(history) - 1, -1, -1):
        if history[i]["type"] == "warn":
            removed = history.pop(i)
            save_data(data)
            await message.answer(
                f"✅ {role} {admin_fullname} зняв попередження у {user_name}.\n"
            )
            return

    await message.reply(f"<b>❗ У користувача {user_name} немає попереджень для зняття.</b>")
    
@dp.message(Command(commands=["help"]))
async def open_panel(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👑 Як стати на Адмінку", callback_data="become_an_admin"),
                InlineKeyboardButton(text="❓ Правила", callback_data="chat_rules"),
            ],
            [
                InlineKeyboardButton(text="👮 Мої покарання", callback_data="my_punishments"),
            ],
            [
                InlineKeyboardButton(text="💬 Більше", callback_data="more_questions"),
            ],
        ]
    )
    await message.answer("<b>Що вас цікавить:</b>", reply_markup=keyboard)


# /report <причина> (reply або просто)
@dp.message(Command("report"))
async def report_user(message: Message):
    global last_report_time
    args = message.text.split()
    if len(args) < 2:
        await message.reply("<b>❗ Вкажіть причину: /report <причина></b>")
        return

    reporter = message.from_user
    reporter_id = str(reporter.id)
    now = datetime.now()

    # === Перевірка кулдауна ===
    if reporter_id in last_report_time:
        time_diff = (now - last_report_time[reporter_id]).total_seconds()
        if time_diff < 180:  # 3 хвилини
            wait_time = int(180 - time_diff)
            await message.reply(
                f"<b>⏳ Ви зможете знову надіслати репорт через 3 хвилини.</b>"
            )
            return
    last_report_time[reporter_id] = now
    # =========================

    reason = " ".join(args[1:])
    reported_user = message.reply_to_message.from_user if message.reply_to_message else None

    reporter_name = reporter.full_name

    if reported_user:
        reported_name = reported_user.full_name
        reported_id = reported_user.id
    else:
        reported_name = "❓ Невідомо (без reply)"
        reported_id = "—"

    now_str = now.strftime("%d.%m.%Y %H:%M:%S")

    report_msg = (
        f"🚨 **Новий репорт!**\n"
        f"👤 Від: {reporter_name} (`{reporter_id}`)\n"
        f"🎯 На: {reported_name} (`{reported_id}`)\n"
        f"🕒 Час: {now_str}\n"
        f"📌 Причина: {reason}"
    )

    async with aiohttp.ClientSession() as session:
        await session.post(DISCORD_WEBHOOK_URL, json={"content": report_msg})

    await message.reply(
        "<b>✅ Ви відправили репорт. Очікуйте на відповідь адміністратора.</b>"
    )
    
async def check_unmute():
    while True:
        now = datetime.now()
        # safe copy to avoid "dictionary changed size during iteration"
        for user_id, mute_info in list(data.get("muted_users", {}).items()):
            try:
                # визначаємо chat_id і until_iso по різних форматах
                if isinstance(mute_info, dict):
                    until_iso = mute_info.get("until")
                    chat_id = mute_info.get("chat_id")
                else:
                    until_iso = mute_info
                    chat_id = None  # немає chat_id — нічого робити із Telegram-частиною

                if not until_iso:
                    # некоректний запис — видаляємо
                    del data["muted_users"][user_id]
                    save_data(data)
                    continue

                until_dt = datetime.fromisoformat(until_iso)

                if until_dt <= now:
                    # якщо знаємо chat_id — відновлюємо права в чаті
                    if chat_id is not None:
                        try:
                            await bot.restrict_chat_member(
                                chat_id=int(chat_id),
                                user_id=int(user_id),
                                permissions=ChatPermissions(
                                    can_send_messages=True,
                                    can_send_media_messages=True,
                                    can_send_other_messages=True,
                                    can_add_web_page_previews=True
                                )
                            )
                            logging.info(f"[check_unmute] Unmuted user {user_id} in chat {chat_id}")
                        except Exception as e:
                            logging.exception(f"[check_unmute] Помилка при знятті муту (user={user_id}, chat={chat_id}): {e}")
                    else:
                        # Якщо chat_id відсутній — лог і просто видалимо локальну мітку
                        logging.warning(f"[check_unmute] Немає chat_id для user {user_id}, просто видаляю запис.")

                    # Видаляємо з бази і зберігаємо
                    if user_id in data.get("muted_users", {}):
                        del data["muted_users"][user_id]
                        save_data(data)

            except Exception as e:
                logging.exception(f"[check_unmute] Непередбачена помилка для user {user_id}: {e}")

        await asyncio.sleep(30)  # перевіряти кожні 30s


# Запуск
async def main():
    # Якщо хочеш скидати webhook — зроби це тут (як в тебе було)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    # Запускаємо таску автозняття мута (без аргументів — використовує глобальний bot)
    asyncio.create_task(check_unmute())

    # Запускаємо polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())