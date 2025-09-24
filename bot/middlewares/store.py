from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from ..data_store import DataStore


class StoreMiddleware(BaseMiddleware):
    def __init__(self, store: DataStore) -> None:
        super().__init__()
        self.store = store

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["store"] = self.store
        return await handler(event, data)

