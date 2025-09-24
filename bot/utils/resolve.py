from typing import Optional

from aiogram import Bot
from aiogram.types import Message, User


async def resolve_user(message: Message, args: list[str], bot: Bot) -> Optional[User]:
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(args) < 2:
        return None
    target = args[-1]
    if target.startswith("@"):  # username
        try:
            user = await bot.get_chat(target)
            return user
        except Exception:
            return None
    elif target.isdigit():
        try:
            user = await bot.get_chat(int(target))
            return user
        except Exception:
            return None
    return None

