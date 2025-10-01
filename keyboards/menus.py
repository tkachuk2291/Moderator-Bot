from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
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


def back_to_help_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
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


def faq_list_kb(questions: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"❓ {q}", callback_data=f"faq_{i+1}")]
        for i, q in enumerate(questions)
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад у головне меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def faq_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад до списку питань", callback_data="more_questions")]]
    )

