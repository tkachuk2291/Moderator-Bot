import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, Bot
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command
from aiogram.filters.command import CommandObject

from filters import IsAdmin
from data_store import DataStore, HistoryEntry, store
from utils.parse import parse_duration_to_seconds

moderation_router = Router()


# ------------------ ЛОГ ПОКАРАНЬ ------------------
def log_punishment(message: Message, target_user, punishment_type, duration_text=None, reason="Не вказано"):
    admin_name = message.from_user.full_name
    target_name = target_user.full_name

    if punishment_type == "ban":
        text = f"⛔ Адміністратор {admin_name} заблокував {target_name} " \
               f"{duration_text if duration_text else 'назавжди'}.\n📋 Причина: {reason}"
    elif punishment_type == "mute":
        text = f"🔇 Адміністратор {admin_name} видав мут {target_name} " \
               f"на {duration_text}.\n📋 Причина: {reason}"
    elif punishment_type == "kick":
        text = f"👢 Адміністратор {admin_name} від’єднав {target_name}.\n📌 Причина: {reason}"
    elif punishment_type == "warn":
        text = f"⚠️ Адміністратор {admin_name} попередив {target_name}.\n📝 Причина: {reason}"
    else:
        text = f"❗ Невідомий тип покарання для {target_name}"

    # Логування в DataStore
    store.append_history(
        target_user.id,
        HistoryEntry(
            type=punishment_type,
            reason=reason,
            date=datetime.now().strftime("%d.%m.%Y %H:%M"),
            text=text
        )
    )
    return text


# ------------------ REPLY REPORT ------------------
@moderation_router.message(Command("replyreport"), IsAdmin())
async def reply_report(message: Message):
    admin_fullname = message.from_user.full_name
    admin_name = message.from_user.first_name
    role = "Адміністратор"
    import random

    phrases = [
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b>\n\nВітаю, {admin_name} мчить вам на допомогу.",
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b> {admin_name} вже в дорозі!",
        f"💬 <b>Відповідь від: {role} {admin_fullname} </b>\n\n{admin_name} поспішає вам на допомогу!",
    ]
    first_text = random.choice(phrases)
    await message.answer(first_text, parse_mode="HTML")
    await asyncio.sleep(random.randint(3, 7))
    second_text = f"💬 <b>Відповідь від {admin_fullname}</b>\n\nВітаю, мене звати {admin_name}, працюю по вашій заявці."
    await message.answer(second_text, parse_mode="HTML")


# ------------------ SPEC ------------------
@moderation_router.message(Command("spec", "spectator"), IsAdmin())
async def spec_user(message: Message, bot: Bot, store: DataStore):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    user_id = str(target_user.id)
    user_name = target_user.full_name
    karma = store.get_karma(user_id, True)
    chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=target_user.id)
    status = chat_member.status
    role = "Адміністратор" if status in ["creator", "administrator"] else "Учасник"
    
    info_text = (
        f"<b>👤 Інформація про користувача:</b>\n"
        f"📝 Ім'я: {user_name}\n"
        f"🏷 Статус: {role}\n"
        f"⚖️ Карма: {karma}"
        f"🆔 ID: {user_id}\n"
    )

    if role == "Учасник":
        punishments: list[HistoryEntry] = store.get_history(target_user.id)
        if punishments:
            info_text += "\n<b>👮 Історія покарань:</b>\n"
            for idx, entry in enumerate(punishments, start=1):
                info_text += (
                    f"{idx}. <i>{entry.date}</i>\n"
                    f"{entry.text}\n\n"
                )
        else:
            info_text += "\n✅ Покарань немає."

    await message.reply(info_text)


# ------------------ UNBAN ------------------
@moderation_router.message(Command("unban"))
async def unban_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    admin_fullname = message.from_user.full_name
    role = "Адміністратор"
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id, only_if_banned=True)
        await message.answer(f"✅ {role} {admin_fullname} розблокував користувача {target_user.full_name}")
    except Exception as e:
        await message.answer(f"❌ Помилка при розбані: {e}")


# ------------------ BAN ------------------
@moderation_router.message(Command("ban"))
async def ban_user(message: Message, command: CommandObject, bot: Bot):
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

    seconds, duration_text = parse_duration_to_seconds(duration_reason)

    until_date = None if seconds is None else datetime.now() + timedelta(seconds=seconds)

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
            until_date=until_date,
        )
        text = log_punishment(message, target_user, "ban", duration_text, reason)
        await message.answer(text)
    except Exception as e:
        await message.reply(f"❌ Помилка при бані: {e}")


# ------------------ MUTE ------------------
@moderation_router.message(Command("mute"))
async def mute_user(message: Message, command: CommandObject, bot: Bot):
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

    seconds, duration_text = parse_duration_to_seconds(duration_reason)
    if not seconds:
        await message.reply("❗ Невірний формат часу. Використай: 10m, 2h, 7d")
        return

    until_date = datetime.now() + timedelta(seconds=seconds)

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )
        text = log_punishment(message, target_user, "mute", duration_text, reason)
        await message.answer(text)
    except Exception as e:
        await message.reply(f"❌ Помилка при муті: {e}")


# ------------------ UNMUTE ------------------
@moderation_router.message(Command("unmute"))
async def unmute_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.answer(f"🔊 Адміністратор {message.from_user.full_name} зняв мут {target_user.full_name}.")
    except Exception as e:
        await message.answer(f"❌ Помилка при знятті мута: {e}")


# ------------------ KICK ------------------
@moderation_router.message(Command("kick"))
async def kick_user(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    reason = "Без причини"
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id,
                                  until_date=datetime.now() + timedelta(seconds=30))
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        text = log_punishment(message, target_user, "kick", reason=reason)
        await message.answer(text)
    except Exception as e:
        await message.reply(f"❌ Помилка при виконанні кіку: {e}")


# ------------------ WARN ------------------
@moderation_router.message(Command("warn"), IsAdmin())
async def warn_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("❗ Використай команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    reason = command.args if command.args else "Без причини"
    text = log_punishment(message, target_user, "warn", reason=reason)
    await message.answer(text)


# ------------------ UNWARN ------------------
@moderation_router.message(Command("unwarn"), IsAdmin())
async def unwarn_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❗ Використайте команду у відповідь на повідомлення користувача.")
        return
    target_user = message.reply_to_message.from_user
    removed = store.pop_last_warn(target_user.id)
    if removed:
        await message.answer(f"✅ Адміністратор {message.from_user.full_name} зняв попередження у {target_user.full_name}.")
    else:
        await message.reply(f"❗ У користувача {target_user.full_name} немає попереджень для зняття.")
