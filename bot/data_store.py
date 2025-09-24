import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import DATA_FILE


class DataStore:
    """Simple JSON-backed store for user moderation data."""

    def __init__(self, file_path: str = DATA_FILE) -> None:
        self.file_path = file_path
        self.data: Dict[str, Any] = {
            "muted_users": {},
            "warnings": {},
            "karma": {},
            "history": {},
            "banned_users": [],
        }
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
        except Exception:
            # Start with empty if file is corrupted
            pass

    def save(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    # History
    def append_history(self, user_id: int, entry: Dict[str, Any]) -> None:
        uid = str(user_id)
        if "history" not in self.data:
            self.data["history"] = {}
        if uid not in self.data["history"]:
            self.data["history"][uid] = []
        self.data["history"][uid].append(entry)
        self.save()

    def get_history(self, user_id: int) -> List[Dict[str, Any]]:
        return self.data.get("history", {}).get(str(user_id), [])

    # Karma
    def get_karma(self, user_id: int, is_admin: bool = False) -> int:
        uid = str(user_id)
        if uid not in self.data.get("karma", {}):
            if "karma" not in self.data:
                self.data["karma"] = {}
            self.data["karma"][uid] = 1000 if is_admin else 0
            self.save()
        return int(self.data["karma"][uid])

    def set_karma(self, user_id: int, value: int) -> int:
        uid = str(user_id)
        if "karma" not in self.data:
            self.data["karma"] = {}
        self.data["karma"][uid] = value
        self.save()
        return value

    # Mutes
    def set_mute(self, chat_id: int, user_id: int, until: Optional[datetime]) -> None:
        uid = str(user_id)
        if "muted_users" not in self.data:
            self.data["muted_users"] = {}
        self.data["muted_users"][uid] = {
            "chat_id": str(chat_id),
            "until": until.isoformat() if until else None,
        }
        self.save()

    def clear_mute(self, user_id: int) -> None:
        uid = str(user_id)
        if uid in self.data.get("muted_users", {}):
            del self.data["muted_users"][uid]
            self.save()

