from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command
from datetime import datetime, timedelta
from contextlib import suppress
import asyncio
from Bot_config import warnings, admin_chat_id, BOT_TOKEN

# Ініціалізація
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

# Команда /mute
@router.message(Command('mute'))
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

    # Додаємо попередження користувачу
    warnings[user_id] = warnings.get(user_id, 0) + 1
    current_warnings = warnings[user_id]

    # Формування часу закінчення мюту
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

        # Попередження для адмінів при досягненні ліміту
        if current_warnings >= 3:
            await bot.send_message(
                admin_chat_id,
                f"⚠️ Користувач {mention} має {current_warnings} попередження! Рекомендуємо розглянути бан.",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply(f"❌ Помилка: {e}")

# Команда /unmute
@router.message(Command('unmute'))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❌ Ви повинні відповісти на повідомлення користувача, якого хочете розм'ючити.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    mention = message.reply_to_message.from_user.mention_html()

    # Скидання попереджень
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

# Команда /ban
@router.message(Command("ban"))
async def ban_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❌ Ви повинні відповісти на повідомлення користувача, якого хочете забанити.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    mention = f"<b>{message.reply_to_message.from_user.full_name}</b>"

    try:
        with suppress(Exception):
            # Заборона користувачеві писати, надсилати медіа та інші повідомлення
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(),  # Всі дозволи скинуті
            )
            await message.reply(
                f"🚫 Користувача {mention} було позбавлено права писати в чат <b>назавжди</b>.",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply(f"❌ Помилка: {e}")

# Команда /unban
@router.message(Command("unban"))
async def unban_user(message: Message):
    if not message.reply_to_message:
        await message.reply("❌ Ви повинні відповісти на повідомлення користувача, якого хочете розбанити.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    mention = f"<b>{message.reply_to_message.from_user.full_name}</b>"

    try:
        with suppress(Exception):
            # Відновлення всіх дозволів для користувача
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
                f"✅ Користувача {mention} було розбанено. Тепер він може писати в чат.",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply(f"❌ Помилка: {e}")

# Команда /report (для двох сценаріїв)
@router.message(Command("report"))
async def report_user(message: Message):
    if message.reply_to_message:
        reporter = f"{message.from_user.full_name} ({message.from_user.mention_html()})"
        reported = f"{message.reply_to_message.from_user.full_name} ({message.reply_to_message.from_user.mention_html()})"
        reason = " ".join(message.text.split()[1:]) or "Без причини"

        await bot.send_message(f'<b>{message.from_user.full_name}</b> Ви відправили Репорт, чекайте від Адміністратора! приємного спілкування.', parse_mode='HTML')

        await bot.send_message(
            admin_chat_id,
            f"🚨 {reporter} повідомив про користувача {reported}.\nПричина: {reason}",
            parse_mode="HTML"
        )
    else:
        reporter = f"{message.from_user.full_name} ({message.from_user.mention_html()})"
        reason = " ".join(message.text.split()[1:]) or "Без причини"
        await bot.send_message(
            admin_chat_id,
            f"🚨 {reporter} надіслав репорт.\nПричина: {reason}",
            parse_mode="HTML"
        )


# Команда /myaccount
@router.message(Command("myaccount"))
async def my_account(message: Message):
    # Отримання інформації про користувача
    user = message.from_user
    full_name = user.full_name
    user_id = user.id

    # Визначення статусу користувача
    member = await bot.get_chat_member(message.chat.id, user_id)
    status = "Адмін" if member.status in ["administrator", "creator"] else "Підписник"

    # Формування відповіді
    response = (
        f"👤 <b>Ім'я:</b> {full_name}\n"
        f"🆔 <b>Мій ID:</b> {user_id}\n"
        f"⚡ <b>Статус:</b> {status}"
    )

    await message.reply(response, parse_mode="HTML")



# Реєстрація хендлерів
dp = Dispatcher()
dp.include_router(router)

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())