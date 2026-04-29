import logging

from telethon.errors import UserNotParticipantError
from telethon.tl.custom import Button
from telethon.tl.functions.channels import GetParticipantRequest

from .glob_variables import BotState
from .buttons import Buttons
from .messages import BotMessageHandler
from utils import db

logger = logging.getLogger(__name__)


async def is_user_in_channel(user_id, channel_usernames=None):
    channels = BotState.CHANNEL_IDS if channel_usernames is None else channel_usernames
    if not channels:
        return []

    channels_user_is_not_in = []
    for channel_ref in channels:
        try:
            entity = await BotState.BOT_CLIENT.get_entity(channel_ref)
            await BotState.BOT_CLIENT(GetParticipantRequest(entity, user_id))
        except UserNotParticipantError:
            channels_user_is_not_in.append(channel_ref)
        except Exception as exc:
            logger.warning("Kanal a'zoligini tekshirib bo'lmadi: %s | %s", channel_ref, exc)
    return channels_user_is_not_in


def join_channel_button(channel_username):
    label = channel_username if str(channel_username).startswith("@") else str(channel_username)
    url = f"https://t.me/{label.lstrip('@')}" if not str(label).startswith("-100") else "https://t.me/"
    return Button.url("Kanalga qo'shilish", url)


async def respond_based_on_channel_membership(event, message_if_in_channels: str = None, buttons=None, channels_user_is_not_in: list = None):
    sender_name = event.sender.first_name or "foydalanuvchi"
    user_id = event.sender_id

    channels_user_is_not_in = await is_user_in_channel(user_id) if channels_user_is_not_in is None else channels_user_is_not_in

    if channels_user_is_not_in and user_id not in BotState.ADMIN_USER_IDS:
        join_channel_buttons = [[join_channel_button(channel)] for channel in channels_user_is_not_in]
        join_channel_buttons.append(Buttons.continue_button)
        await BotMessageHandler.send_message(event, f"Salom, {sender_name}! 👋\n{BotMessageHandler.JOIN_CHANNEL_MESSAGE}", buttons=join_channel_buttons)
    elif message_if_in_channels is not None or user_id in BotState.ADMIN_USER_IDS:
        await BotMessageHandler.send_message(event, message_if_in_channels or "", buttons=buttons)


async def handle_continue_in_membership_message(event):
    sender_name = event.sender.first_name or "foydalanuvchi"
    user_id = event.sender_id
    channels_user_is_not_in = await is_user_in_channel(user_id)
    if channels_user_is_not_in:
        join_channel_buttons = [[join_channel_button(channel)] for channel in channels_user_is_not_in]
        join_channel_buttons.append(Buttons.continue_button)
        await BotMessageHandler.edit_message(event, f"Salom, {sender_name}! 👋\n{BotMessageHandler.JOIN_CHANNEL_MESSAGE}", buttons=join_channel_buttons)
        await event.answer("Davom etish uchun kanalga qo'shiling.", alert=True)
        return

    if not await db.check_username_in_database(user_id):
        await db.create_user_settings(user_id)
    await event.delete()
    await respond_based_on_channel_membership(event, f"Salom, {sender_name}! 👋\n{BotMessageHandler.start_message}", buttons=Buttons.main_menu_buttons)
