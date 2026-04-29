import logging

from utils.database import db

logger = logging.getLogger(__name__)


class BroadcastManager:
    """Admin yuboradigan ommaviy xabarlar uchun yordamchi sinf."""

    @staticmethod
    async def broadcast_message_to_sub_members(client, message, button=None):
        user_ids = await db.get_subscribed_user_ids()
        for user_id in user_ids:
            try:
                await client.send_message(user_id, message, buttons=button)
            except Exception as exc:
                logger.warning("Obunachiga xabar yuborilmadi: %s | %s", user_id, exc)

    @staticmethod
    async def broadcast_message_to_temp_members(client, message):
        user_ids = await db.get_temporary_subscribed_user_ids()
        for user_id in user_ids:
            try:
                await client.send_message(user_id, message)
            except Exception as exc:
                logger.warning("Vaqtinchalik foydalanuvchiga xabar yuborilmadi: %s | %s", user_id, exc)

    @staticmethod
    async def add_sub_user(user_id):
        await db.add_subscribed_user(user_id)

    @staticmethod
    async def remove_sub_user(user_id):
        await db.remove_subscribed_user(user_id)

    @staticmethod
    async def get_all_sub_user_ids():
        return await db.get_subscribed_user_ids()

    @staticmethod
    async def clear_user_ids():
        await db.clear_subscribed_users()

    @staticmethod
    async def get_temporary_subscribed_user_ids():
        return await db.get_temporary_subscribed_user_ids()

    @staticmethod
    async def add_all_users_to_temp():
        await db.mark_temporary_subscriptions()

    @staticmethod
    async def remove_all_users_from_temp():
        await db.mark_temporary_unsubscriptions()

    @staticmethod
    async def add_user_to_temp(user_id):
        await db.add_user_to_temp(user_id)
