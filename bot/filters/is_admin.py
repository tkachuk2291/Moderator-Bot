from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        chat_admins = await message.bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
        return message.from_user.id in admin_ids

