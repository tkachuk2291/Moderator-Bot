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
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import os
from typing import Union
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

# ----------------- Завантаження FAQ -----------------
def load_faq():
    if not os.path.exists(FAQ_FILE):
        raise FileNotFoundError(f"Файл FAQ не знайдено: {FAQ_FILE}")

    # читаємо Excel
    df = pd.read_excel(FAQ_FILE)

    # нормалізуємо назви колонок
    df.columns = [c.strip().lower() for c in df.columns]

    # перевірка обов'язкових колонок
    if not {"ваше питання", "відповідь"}.issubset(df.columns):
        raise ValueError("У файлі відсутні колонки 'Ваше питання' або 'Відповідь'")

    # приводимо до тексту і прибираємо зайві пробіли
    df["ваше питання"] = df["ваше питання"].astype(str).str.strip()
    df["відповідь"] = df["відповідь"].astype(str).str.strip()

    # фільтруємо пусті рядки
    df = df[(df["ваше питання"] != "") & (df["відповідь"] != "")]

    # повертаємо список кортежів (питання, відповідь)
    return list(df[["ваше питання", "відповідь"]].itertuples(index=False, name=None))

# ----------------- Хендлер: список питань -----------------
@dp.callback_query(lambda c: c.data == "more_questions")
async def process_more_questions(callback: CallbackQuery):
    await callback.answer()
    try:
        faq_list = load_faq()

        # робимо список кнопок (кожне питання)
        buttons = [
            [InlineKeyboardButton(text=f"❓ {q}", callback_data=f"faq_{i+1}")]
            for i, (q, _) in enumerate(faq_list)
        ]

        # додаємо кнопку "Назад у головне меню"
        buttons.append(
            [InlineKeyboardButton(text="⬅️ Назад у головне меню", callback_data="main_menu")]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(
            "<b>📋 Список питань:</b>\n\nОберіть, щоб побачити відповідь 👇",
            reply_markup=keyboard
        )

    except Exception as e:
        await callback.message.edit_text(f"<b>❗ Помилка при завантаженні FAQ:</b> {str(e)}")


@dp.callback_query(lambda c: c.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    await callback.answer()
    try:
        faq_list = load_faq()
        idx = int(callback.data.split("_")[1]) - 1

        if idx < 0 or idx >= len(faq_list):
            await callback.message.edit_text("<b>❗ Питання не знайдено.</b>")
            return

        question, answer = faq_list[idx]

        # Якщо відповідь виглядає як посилання → робимо HTML-лінк
        if answer.startswith("http://") or answer.startswith("https://"):
            text = f"<b>❓ {question}</b>\n\n✅ Можна дізнатися: <a href='{answer}'>тут</a>"
        else:
            text = f"<b>❓ {question}</b>\n\n✅ {answer}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад до списку питань", callback_data="more_questions")]
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        await callback.message.edit_text(f"<b>❗ Помилка при завантаженні FAQ:</b> {str(e)}")

# ----------------- Повернення в головне меню -----------------
@dp.callback_query(lambda c: c.data == "back_help")
async def back_to_help(callback: CallbackQuery):
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
    await callback.message.edit_text("<b>Що вас цікавить:</b>", reply_markup=keyboard)
    await callback.answer()


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


# ----------------- Хендлер: Як стати адміністратором -----------------
@dp.callback_query(lambda c: c.data == "become_an_admin")
async def become_admin(callback: CallbackQuery):
    google_form_url = "https://forms.gle/FYfZNa3LYrCYtNnd8"
    text = (
        "<b>👑 Як стати адміністратором:</b>\n\n"
        "Подайте заявку через офіційну Google форму:\n"
        f"<a href='{google_form_url}'>📋 Подати заявку</a>"
    )
    await callback.message.answer(text, disable_web_page_preview=True)
    await callback.answer()

# ----------------- Хендлер: Правила чату -----------------
@dp.callback_query(lambda c: c.data == "chat_rules")
async def chat_rules(callback: CallbackQuery):
    chat_rules_url = ""
    text = f"<b>❓ Ознайомитися з правилами:</b> <a href='{chat_rules_url}'>✅ Ознайомитися</a>"
    await callback.message.answer(text, disable_web_page_preview=True)
    await callback.answer()

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

@dp.message(Command("spec", "spectator"), IsAdmin())
async def spec_user(message: Message):
    # Перевірка, що команда відповідає на повідомлення
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    user_id = str(target_user.id)
    user_name = target_user.full_name

    # Визначаємо роль користувача
    chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=target_user.id)
    status = chat_member.status  # creator, administrator, member, restricted, left, kicked
    role = "Адміністратор" if status in ["creator", "administrator"] else "Учасник"

    # Основна інформація
    info_text = (
        f"<b>👤 Інформація про користувача:</b>\n"
        f"📝 Ім'я: {user_name}\n"
        f"🏷 Статус/Роль: {role}\n"
        f"🆔 ID: {user_id}\n"
    )

    # Якщо користувач — учасник, додаємо історію покарань
    if role == "Учасник":
        if "history" in data and user_id in data["history"]:
            punishments = data["history"][user_id]
            info_text += "\n<b>👮 Історія покарань:</b>\n"
            for idx, p in enumerate(punishments, start=1):
                info_text += (
                    f"{idx}. ⛔ <b>Тип:</b> {p['type']}\n"
                    f"   📌 <b>Причина:</b> {p['reason']}\n"
                    f"   ⏰ <b>Дата:</b> {p['date']}\n"
                    f"   📅 <b>До:</b> {p.get('until', '—')}\n\n"
                )
        else:
            info_text += "\n✅ Покарань немає."

    await message.reply(info_text)


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


# ----------------- BAN -----------------
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

    try:
        until_date = None if seconds is None else datetime.now() + timedelta(seconds=seconds)

        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False,
                                        can_send_media_messages=False,
                                        can_send_other_messages=False,
                                        can_add_web_page_previews=False),
            until_date=until_date
        )

        await message.answer(f"⛔ Адміністратор {message.from_user.full_name} заблокував {target_user.full_name} "
                             f"{duration_text if duration_text else 'назавжди'}.\n📋 Причина: {reason}")

        # Логування
        user_id = str(target_user.id)
        if "history" not in data:
            data["history"] = {}
        if user_id not in data["history"]:
            data["history"][user_id] = []

        data["history"][user_id].append({
            "type": "ban",
            "reason": reason,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "until": until_date.strftime("%d.%m.%Y %H:%M") if until_date else "Назавжди"
        })
        save_data(data)

    except Exception as e:
        await message.reply(f"❌ Помилка при бані: {e}")


# ----------------- MUTE -----------------
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

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )

        await message.answer(f"🔇 Адміністратор {message.from_user.full_name} видав мут "
                             f"{target_user.full_name} на {duration_text}.\n📋 Причина: {reason}")

        # Логування
        user_id = str(target_user.id)
        if "history" not in data:
            data["history"] = {}
        if user_id not in data["history"]:
            data["history"][user_id] = []

        data["history"][user_id].append({
            "type": "mute",
            "reason": reason,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "until": until_date.strftime("%d.%m.%Y %H:%M")
        })
        save_data(data)

    except Exception as e:
        await message.reply(f"❌ Помилка при муті: {e}")


# ----------------- UNMUTE -----------------
@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=True,
                                        can_send_media_messages=True,
                                        can_send_other_messages=True,
                                        can_add_web_page_previews=True)
        )

        await message.answer(f"🔊 Адміністратор {message.from_user.full_name} зняв мут {target_user.full_name}.")

    except Exception as e:
        await message.answer(f"❌ Помилка при знятті мута: {e}")


# ----------------- KICK -----------------
@dp.message(Command("kick"))
async def kick_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    reason = "Без причини"

    try:
        # кік (бан на 30 сек + розбан)
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id,
                                  until_date=datetime.now() + timedelta(seconds=30))
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)

        # Логування
        user_id = str(target_user.id)
        if "history" not in data:
            data["history"] = {}
        if user_id not in data["history"]:
            data["history"][user_id] = []

        data["history"][user_id].append({
            "type": "kick",
            "reason": reason,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "until": "—"
        })
        save_data(data)

        await message.answer(f"👢 Адміністратор {message.from_user.full_name} від’єднав {target_user.full_name}.\n📌 Причина: {reason}")

    except Exception as e:
        await message.reply(f"❌ Помилка при виконанні кіку: {e}")


# ----------------- WARN -----------------
@dp.message(Command("warn"))
async def warn_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    reason = command.args if command.args else "Без причини"

    # Логування
    user_id = str(target_user.id)
    if "history" not in data:
        data["history"] = {}
    if user_id not in data["history"]:
        data["history"][user_id] = []

    data["history"][user_id].append({
        "type": "warn",
        "reason": reason,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "until": "—"
    })
    save_data(data)

    await message.answer(f"⚠️ Адміністратор {message.from_user.full_name} попередив {target_user.full_name}.\n📝 Причина: {reason}")


# ----------------- Хендлер: Мої покарання -----------------
async def show_punishments(message_or_callback):
    user_id = str(message_or_callback.from_user.id)

    if "history" in data and user_id in data["history"]:
        punishments = data["history"][user_id]
        text = "<b>👮 Ваші покарання:</b>\n\n"
        for p in punishments:
            text += (
                f"⛔ <b>Тип:</b> {p['type']}\n"
                f"📌 <b>Причина:</b> {p['reason']}\n"
                f"⏰ <b>Дата:</b> {p['date']}\n"
                f"📅 <b>До:</b> {p.get('until', '—')}\n\n"
            )
    else:
        text = "<b>✅ У вас немає покарань!</b>"

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text)
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text)


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