import asyncio
import json
from pathlib import Path

import aiosqlite


class db:
    """Bot uchun SQLite yordamchi qatlami."""

    db_name = str(Path("user_settings.db"))
    lock = asyncio.Lock()
    default_downloading_core: str = "Auto"
    default_music_quality: dict = {"format": "mp3", "quality": "320"}
    default_tweet_capture_setting: dict = {"night_mode": "0"}

    @staticmethod
    async def initialize_database() -> None:
        async with aiosqlite.connect(db.db_name) as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    music_quality TEXT NOT NULL,
                    downloading_core TEXT NOT NULL,
                    tweet_capture_settings TEXT NOT NULL,
                    is_file_processing INTEGER DEFAULT 0,
                    is_user_updated INTEGER DEFAULT 1
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    subscribed INTEGER DEFAULT 1,
                    temporary INTEGER DEFAULT 0
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS musics (
                    filename TEXT PRIMARY KEY,
                    downloads INTEGER DEFAULT 1
                )
                """
            )
            await conn.commit()

    @staticmethod
    async def _execute(query: str, params: tuple = ()) -> None:
        async with db.lock:
            async with aiosqlite.connect(db.db_name) as conn:
                await conn.execute(query, params)
                await conn.commit()

    @staticmethod
    async def _fetch_one(query: str, params: tuple = ()):
        async with db.lock:
            async with aiosqlite.connect(db.db_name) as conn:
                cursor = await conn.execute(query, params)
                row = await cursor.fetchone()
                await cursor.close()
                return row

    @staticmethod
    async def _fetch_all(query: str, params: tuple = ()):
        async with db.lock:
            async with aiosqlite.connect(db.db_name) as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                await cursor.close()
                return rows

    @staticmethod
    async def create_user_settings(user_id: int) -> None:
        music_quality = json.dumps(db.default_music_quality)
        tweet_capture = json.dumps(db.default_tweet_capture_setting)
        await db._execute(
            """
            INSERT OR IGNORE INTO user_settings (
                user_id, music_quality, downloading_core, tweet_capture_settings, is_file_processing, is_user_updated
            ) VALUES (?, ?, ?, ?, 0, 1)
            """,
            (user_id, music_quality, db.default_downloading_core, tweet_capture),
        )
        await db._execute(
            """
            INSERT OR IGNORE INTO subscriptions (user_id, subscribed, temporary)
            VALUES (?, 1, 0)
            """,
            (user_id,),
        )

    @staticmethod
    async def check_username_in_database(user_id: int) -> bool:
        result = await db._fetch_one("SELECT 1 FROM user_settings WHERE user_id = ?", (user_id,))
        return result is not None

    @staticmethod
    async def get_user_music_quality(user_id: int) -> dict:
        result = await db._fetch_one("SELECT music_quality FROM user_settings WHERE user_id = ?", (user_id,))
        return json.loads(result[0]) if result and result[0] else {}

    @staticmethod
    async def get_user_downloading_core(user_id: int):
        result = await db._fetch_one("SELECT downloading_core FROM user_settings WHERE user_id = ?", (user_id,))
        return result[0] if result else None

    @staticmethod
    async def set_user_music_quality(user_id: int, music_quality: dict) -> None:
        await db._execute(
            "UPDATE user_settings SET music_quality = ? WHERE user_id = ?",
            (json.dumps(music_quality), user_id),
        )

    @staticmethod
    async def set_user_downloading_core(user_id: int, downloading_core: str) -> None:
        await db._execute(
            "UPDATE user_settings SET downloading_core = ? WHERE user_id = ?",
            (downloading_core, user_id),
        )

    @staticmethod
    async def get_all_user_ids() -> list[int]:
        return [row[0] for row in await db._fetch_all("SELECT user_id FROM user_settings")]

    @staticmethod
    async def count_all_user_ids() -> int:
        result = await db._fetch_one("SELECT COUNT(*) FROM user_settings")
        return int(result[0]) if result else 0

    @staticmethod
    async def add_user_to_temp(user_id: int) -> None:
        await db._execute("UPDATE subscriptions SET temporary = 1 WHERE user_id = ?", (user_id,))

    @staticmethod
    async def remove_user_from_temp(user_id: int) -> None:
        await db._execute("UPDATE subscriptions SET temporary = 0 WHERE user_id = ?", (user_id,))

    @staticmethod
    async def add_subscribed_user(user_id: int) -> None:
        await db._execute(
            "INSERT OR IGNORE INTO subscriptions (user_id, subscribed, temporary) VALUES (?, 1, 0)",
            (user_id,),
        )
        await db._execute("UPDATE subscriptions SET subscribed = 1 WHERE user_id = ?", (user_id,))

    @staticmethod
    async def remove_subscribed_user(user_id: int) -> None:
        await db._execute("UPDATE subscriptions SET subscribed = 0 WHERE user_id = ?", (user_id,))

    @staticmethod
    async def get_subscribed_user_ids() -> list[int]:
        return [row[0] for row in await db._fetch_all("SELECT user_id FROM subscriptions WHERE subscribed = 1")]

    @staticmethod
    async def clear_subscribed_users() -> None:
        await db._execute("UPDATE subscriptions SET subscribed = 0")

    @staticmethod
    async def mark_temporary_subscriptions() -> None:
        await db._execute("UPDATE subscriptions SET temporary = 1")

    @staticmethod
    async def mark_temporary_unsubscriptions() -> None:
        await db._execute("UPDATE subscriptions SET temporary = 0")

    @staticmethod
    async def get_temporary_subscribed_user_ids() -> list[int]:
        return [row[0] for row in await db._fetch_all("SELECT user_id FROM subscriptions WHERE temporary = 1")]

    @staticmethod
    async def is_user_subscribed(user_id: int) -> bool:
        result = await db._fetch_one("SELECT subscribed FROM subscriptions WHERE user_id = ?", (user_id,))
        return bool(result and result[0])

    @staticmethod
    async def count_subscribed_users() -> int:
        result = await db._fetch_one("SELECT COUNT(*) FROM subscriptions WHERE subscribed = 1")
        return int(result[0]) if result else 0

    @staticmethod
    async def set_user_updated_flag(user_id: int, is_user_updated: bool) -> None:
        await db._execute(
            "UPDATE user_settings SET is_user_updated = ? WHERE user_id = ?",
            (1 if is_user_updated else 0, user_id),
        )

    @staticmethod
    async def get_user_updated_flag(user_id: int) -> bool:
        result = await db._fetch_one("SELECT is_user_updated FROM user_settings WHERE user_id = ?", (user_id,))
        return bool(result and result[0])

    @staticmethod
    async def set_file_processing_flag(user_id: int, is_processing: bool) -> None:
        await db._execute(
            "UPDATE user_settings SET is_file_processing = ? WHERE user_id = ?",
            (1 if is_processing else 0, user_id),
        )

    @staticmethod
    async def get_file_processing_flag(user_id: int) -> bool:
        result = await db._fetch_one("SELECT is_file_processing FROM user_settings WHERE user_id = ?", (user_id,))
        return bool(result and result[0])

    @staticmethod
    async def reset_all_file_processing_flags() -> None:
        await db._execute("UPDATE user_settings SET is_file_processing = 0")

    @staticmethod
    async def increment_download_counter(filename: str) -> None:
        await db._execute("UPDATE musics SET downloads = downloads + 1 WHERE filename = ?", (filename,))

    @staticmethod
    async def add_or_increment_song(filename: str) -> None:
        result = await db._fetch_one("SELECT downloads FROM musics WHERE filename = ?", (filename,))
        if result:
            await db.increment_download_counter(filename)
        else:
            await db._execute("INSERT INTO musics (filename, downloads) VALUES (?, 1)", (filename,))

    @staticmethod
    async def get_total_downloads() -> int:
        result = await db._fetch_one("SELECT COALESCE(SUM(downloads), 0) FROM musics")
        return int(result[0]) if result else 0

    @staticmethod
    async def get_song_downloads(filename: str) -> int:
        result = await db._fetch_one("SELECT downloads FROM musics WHERE filename = ?", (filename,))
        return int(result[0]) if result else 0

    @staticmethod
    async def set_user_tweet_capture_settings(user_id: int, tweet_capture_settings: dict) -> None:
        await db._execute(
            "UPDATE user_settings SET tweet_capture_settings = ? WHERE user_id = ?",
            (json.dumps(tweet_capture_settings), user_id),
        )

    @staticmethod
    async def get_user_tweet_capture_settings(user_id: int) -> dict:
        result = await db._fetch_one("SELECT tweet_capture_settings FROM user_settings WHERE user_id = ?", (user_id,))
        return json.loads(result[0]) if result and result[0] else {}
