import asyncio
import logging
from datetime import datetime

from aiogram.types import ChatPermissions
from aiogram import Bot

from ..data_store import DataStore


async def check_unmute(bot: Bot, store: DataStore) -> None:
    while True:
        now = datetime.now()
        for user_id, mute_info in list(store.data.get("muted_users", {}).items()):
            try:
                if isinstance(mute_info, dict):
                    until_iso = mute_info.get("until")
                    chat_id = mute_info.get("chat_id")
                else:
                    until_iso = mute_info
                    chat_id = None
                if not until_iso:
                    del store.data["muted_users"][user_id]
                    store.save()
                    continue
                until_dt = datetime.fromisoformat(until_iso)
                if until_dt <= now:
                    if chat_id is not None:
                        try:
                            await bot.restrict_chat_member(
                                chat_id=int(chat_id),
                                user_id=int(user_id),
                                permissions=ChatPermissions(
                                    can_send_messages=True,
                                    can_send_media_messages=True,
                                    can_send_other_messages=True,
                                    can_add_web_page_previews=True,
                                ),
                            )
                            logging.info(f"[check_unmute] Unmuted user {user_id} in chat {chat_id}")
                        except Exception as e:
                            logging.exception(
                                f"[check_unmute] Помилка при знятті муту (user={user_id}, chat={chat_id}): {e}"
                            )
                    else:
                        logging.warning(f"[check_unmute] Немає chat_id для user {user_id}, просто видаляю запис.")
                    if user_id in store.data.get("muted_users", {}):
                        del store.data["muted_users"][user_id]
                        store.save()
            except Exception as e:
                logging.exception(f"[check_unmute] Непередбачена помилка для user {user_id}: {e}")
        await asyncio.sleep(30)

