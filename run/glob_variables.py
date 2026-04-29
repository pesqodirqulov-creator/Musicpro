import asyncio
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from telethon import TelegramClient


load_dotenv()
load_dotenv("config.env")


def _parse_admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_ID") or os.getenv("ADMIN_IDS") or os.getenv("ADMIN_USER_IDS") or ""
    result: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            result.append(int(item))
        except ValueError:
            continue
    return result


def _parse_channels() -> list[str]:
    raw = os.getenv("CHANNEL_ID", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class UserState:
    admin_message_to_send: object = None
    admin_broadcast: bool = False
    send_to_specified_flag: bool = False
    search_result: str | None = None


class BotState:
    """Botning umumiy holati shu yerda saqlanadi."""

    user_states: dict[int, UserState] = {}
    lock = asyncio.Lock()

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    CHANNEL_IDS = _parse_channels()
    ADMIN_USER_IDS = _parse_admin_ids()
    BOT_CLIENT: TelegramClient | None = None

    @classmethod
    def refresh_env(cls) -> None:
        cls.BOT_TOKEN = os.getenv("BOT_TOKEN")
        cls.API_ID = os.getenv("API_ID")
        cls.API_HASH = os.getenv("API_HASH")
        cls.CHANNEL_IDS = _parse_channels()
        cls.ADMIN_USER_IDS = _parse_admin_ids()

    @classmethod
    def validate_required_env(cls) -> None:
        cls.refresh_env()
        missing = [
            name
            for name, value in (
                ("BOT_TOKEN", cls.BOT_TOKEN),
                ("API_ID", cls.API_ID),
                ("API_HASH", cls.API_HASH),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Quyidagi muhit o'zgaruvchilari topilmadi: "
                + ", ".join(missing)
                + ". .env yoki Railway Variables bo'limida ularni kiriting."
            )

    @classmethod
    def ensure_client(cls) -> TelegramClient:
        cls.validate_required_env()
        if cls.BOT_CLIENT is None:
            cls.BOT_CLIENT = TelegramClient("bot", int(cls.API_ID), cls.API_HASH)
        return cls.BOT_CLIENT

    @staticmethod
    async def initialize_user_state(user_id: int) -> None:
        if user_id not in BotState.user_states:
            BotState.user_states[user_id] = UserState()

    @staticmethod
    async def get_user_state(user_id: int) -> UserState:
        async with BotState.lock:
            await BotState.initialize_user_state(user_id)
            return BotState.user_states[user_id]

    @staticmethod
    async def get_admin_message_to_send(user_id: int):
        return (await BotState.get_user_state(user_id)).admin_message_to_send

    @staticmethod
    async def get_admin_broadcast(user_id: int) -> bool:
        return (await BotState.get_user_state(user_id)).admin_broadcast

    @staticmethod
    async def get_send_to_specified_flag(user_id: int) -> bool:
        return (await BotState.get_user_state(user_id)).send_to_specified_flag

    @staticmethod
    async def set_admin_message_to_send(user_id: int, message) -> None:
        (await BotState.get_user_state(user_id)).admin_message_to_send = message

    @staticmethod
    async def set_admin_broadcast(user_id: int, value: bool) -> None:
        (await BotState.get_user_state(user_id)).admin_broadcast = value

    @staticmethod
    async def set_send_to_specified_flag(user_id: int, value: bool) -> None:
        (await BotState.get_user_state(user_id)).send_to_specified_flag = value
