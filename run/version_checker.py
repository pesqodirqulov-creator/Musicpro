from utils import db


async def update_bot_version_user_season(event) -> bool:
    """Eski holatlarni muammosiz tiklash uchun foydalanuvchini avtomatik yaratadi."""
    user_id = event.sender_id
    if not await db.check_username_in_database(user_id):
        await db.create_user_settings(user_id)
    await db.set_user_updated_flag(user_id, True)
    return True
