from aiogram import Router
from aiogram.types import Message

from ..data_store import DataStore


karma_router = Router()
store = DataStore()


@karma_router.message()
async def handle_karma(message: Message):
    if not message.reply_to_message:
        return
    target_user = message.reply_to_message.from_user
    user_id = str(target_user.id)
    text = (message.text or "").strip()
    if not text:
        return
    if text.isdigit() or (text.startswith("+") and text[1:].isdigit()):
        value = int(text.replace("+", ""))
        new_karma = min(1000, store.get_karma(target_user.id) + value)
    elif text.startswith("-") and text[1:].isdigit():
        value = int(text)
        new_karma = max(-1000, store.get_karma(target_user.id) + value)
    else:
        return
    store.set_karma(target_user.id, new_karma)
    await message.reply(
        f"⚖️ Карма користувача {target_user.full_name}: <b>{new_karma}</b>\n"
        f"(Максимум: 1000 | Мінімум: -1000)"
    )


@karma_router.callback_query(lambda c: c.data == "my_punishments")
async def show_punishments(callback):
    user_id = str(callback.from_user.id)
    punishments = store.get_history(int(user_id))
    if punishments:
        text = "<b>👮 Ваші покарання:</b>\n\n"
        for p in punishments:
            text += (
                f"⛔ <b>Тип:</b> {p.get('type','')}\n"
                f"📌 <b>Причина:</b> {p.get('reason','')}\n"
                f"⏰ <b>Дата:</b> {p.get('date','')}\n"
                f"📅 <b>До:</b> {p.get('until','—')}\n\n"
            )
    else:
        text = "<b>✅ У вас немає покарань!</b>"
    await callback.message.answer(text)
    await callback.answer()

