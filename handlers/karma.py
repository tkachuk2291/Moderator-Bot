from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from re import Match

from data_store import DataStore

karma_router = Router()


@karma_router.message(F.reply_to_message, F.text.regexp(r"^\+?\d+$").as_("digits"))
async def handle_karma_plus(message: Message, digits: Match[str], store: DataStore):
    target_user = message.reply_to_message.from_user
    value = int(digits.group(0).replace("+", ""))
    new_karma = store.add_karma(target_user.id, value)
    await message.reply(
        f"⚖️ Карма користувача {target_user.full_name}: <b>{new_karma}</b>\n"
        f"(Максимум: 1000 | Мінімум: -1000)"
    )


@karma_router.message(F.reply_to_message, F.text.regexp(r"^-\d+$").as_("digits"))
async def handle_karma_minus(message: Message, digits: Match[str], store: DataStore):
    target_user = message.reply_to_message.from_user
    value = int(digits.group(0))
    new_karma = store.add_karma(target_user.id, value)
    await message.reply(
        f"⚖️ Карма користувача {target_user.full_name}: <b>{new_karma}</b>\n"
        f"(Максимум: 1000 | Мінімум: -1000)"
    )