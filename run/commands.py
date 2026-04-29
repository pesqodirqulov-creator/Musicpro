from plugins.spotify import SpotifyDownloader
from utils import db, asyncio, BroadcastManager, time, sanitize_query
from .glob_variables import BotState
from .buttons import Buttons
from .messages import BotMessageHandler
from .channel_checker import respond_based_on_channel_membership
from .version_checker import update_bot_version_user_season


ADMIN_USER_IDS = BotState.ADMIN_USER_IDS


class BotCommandHandler:
    @staticmethod
    async def start(event):
        sender_name = event.sender.first_name or "do'st"
        user_id = event.sender_id
        if not await db.check_username_in_database(user_id):
            await db.create_user_settings(user_id)
        await respond_based_on_channel_membership(event, f"Salom, {sender_name}! 👋\n{BotMessageHandler.start_message}", buttons=Buttons.main_menu_buttons)

    @staticmethod
    async def handle_stats_command(event):
        if event.sender_id not in ADMIN_USER_IDS:
            return
        number_of_users = await db.count_all_user_ids()
        number_of_subscribed = await db.count_subscribed_users()
        number_of_unsubscribed = number_of_users - number_of_subscribed
        await event.respond(
            f"📊 Statistika\n\n"
            f"Jami foydalanuvchilar: {number_of_users}\n"
            f"Obunachilar: {number_of_subscribed}\n"
            f"Obunani o'chirganlar: {number_of_unsubscribed}"
        )

    @staticmethod
    async def handle_admin_command(event):
        if event.sender_id not in ADMIN_USER_IDS:
            return
        await BotMessageHandler.send_message(event, "👮 Admin bo'limi", buttons=Buttons.admins_buttons)

    @staticmethod
    async def handle_ping_command(event):
        start_time = time.time()
        ping_message = await event.reply("🏓 Pong!")
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        await ping_message.edit(f"🏓 Pong!\nJavob vaqti: {response_time:3.3f} ms")

    @staticmethod
    async def handle_core_command(event):
        if await update_bot_version_user_season(event):
            user_id = event.sender_id
            downloading_core = await db.get_user_downloading_core(user_id) or "Auto"
            await respond_based_on_channel_membership(
                event,
                BotMessageHandler.core_selection_message + f"\n\nJoriy usul: {downloading_core}",
                buttons=Buttons.get_core_setting_buttons(downloading_core),
            )

    @staticmethod
    async def handle_quality_command(event):
        if await update_bot_version_user_season(event):
            user_id = event.sender_id
            music_quality = await db.get_user_music_quality(user_id)
            await respond_based_on_channel_membership(
                event,
                f"🎚 Joriy sifat sozlamasi:\nFormat: {music_quality['format']}\nSifat: {music_quality['quality']}\n\nMavjud variantlar:",
                buttons=Buttons.get_quality_setting_buttons(music_quality),
            )

    @staticmethod
    async def handle_help_command(event):
        if await update_bot_version_user_season(event):
            await respond_based_on_channel_membership(event, BotMessageHandler.instruction_message, buttons=Buttons.back_button)

    @staticmethod
    async def handle_unsubscribe_command(event):
        if await update_bot_version_user_season(event):
            user_id = event.sender_id
            if not await db.is_user_subscribed(user_id):
                await respond_based_on_channel_membership(event, "Siz hozir obuna bo'lmagansiz.")
                return
            await db.remove_subscribed_user(user_id)
            await respond_based_on_channel_membership(event, "Obuna muvaffaqiyatli bekor qilindi.")

    @staticmethod
    async def handle_subscribe_command(event):
        if await update_bot_version_user_season(event):
            user_id = event.sender_id
            if await db.is_user_subscribed(user_id):
                await respond_based_on_channel_membership(event, "Siz allaqachon obuna bo'lgansiz.")
                return
            await db.add_subscribed_user(user_id)
            await respond_based_on_channel_membership(event, "Obuna muvaffaqiyatli faollashtirildi.")

    @staticmethod
    async def handle_settings_command(event):
        if await update_bot_version_user_season(event):
            await respond_based_on_channel_membership(event, "⚙️ Sozlamalar", buttons=Buttons.setting_button)

    @staticmethod
    async def handle_broadcast_command(event):
        user_id = event.sender_id
        if user_id not in ADMIN_USER_IDS:
            return

        await BotState.set_admin_broadcast(user_id, True)
        command_parts = event.message.text.split(' ', 1)
        send_to_all = event.message.text.startswith('/broadcast_to_all')

        if send_to_all:
            await BroadcastManager.add_all_users_to_temp()
        elif event.message.text.startswith('/broadcast') and len(command_parts) > 1:
            if not command_parts[1].startswith('(') or not command_parts[1].endswith(')'):
                await event.respond("Noto'g'ri format. To'g'ri ko'rinish: /broadcast (123,456)")
                await BotState.set_admin_broadcast(user_id, False)
                await BotState.set_admin_message_to_send(user_id, None)
                return
            await BroadcastManager.remove_all_users_from_temp()
            for raw_user_id in command_parts[1][1:-1].split(','):
                raw_user_id = raw_user_id.strip()
                if raw_user_id.isdigit():
                    await BroadcastManager.add_user_to_temp(int(raw_user_id))

        time_limit = 60
        time_to_send = await event.respond(f"Xabar yuborish uchun {time_limit} soniya vaqtingiz bor.", buttons=Buttons.cancel_broadcast_button)

        for remaining_time in range(time_limit - 1, 0, -1):
            await time_to_send.edit(f"Xabar yuborish uchun {remaining_time} soniya qoldi.")
            if not await BotState.get_admin_broadcast(user_id):
                await time_to_send.edit("Yuborish bekor qilindi.", buttons=None)
                break
            if await BotState.get_admin_message_to_send(user_id) is not None:
                break
            await asyncio.sleep(1)

        if await BotState.get_admin_message_to_send(user_id) is None and await BotState.get_admin_broadcast(user_id):
            await event.respond("Yuborish uchun xabar topilmadi.")
            await BotState.set_admin_broadcast(user_id, False)
            await BotState.set_admin_message_to_send(user_id, None)
            await BroadcastManager.remove_all_users_from_temp()
            return

        try:
            if send_to_all or len(command_parts) > 1:
                await BroadcastManager.broadcast_message_to_temp_members(event.client, await BotState.get_admin_message_to_send(user_id))
            else:
                await BroadcastManager.broadcast_message_to_sub_members(event.client, await BotState.get_admin_message_to_send(user_id), Buttons.cancel_subscription_button_quite)
            await event.respond("Xabar yuborish boshlandi.")
        except Exception as exc:
            await event.respond(f"Xabar yuborishda xatolik: {exc}")
        finally:
            await BroadcastManager.remove_all_users_from_temp()
            await BotState.set_admin_broadcast(user_id, False)
            await BotState.set_admin_message_to_send(user_id, None)

    @staticmethod
    async def handle_search_command(event):
        await update_bot_version_user_season(event)
        search_query = event.message.text[8:].strip()
        if not search_query:
            await event.respond("/search buyrug'idan keyin qidiruv matnini kiriting yoki oddiy xabar yuboring.")
            return

        waiting_message_search = await event.respond('⏳')
        sanitized_query = await sanitize_query(search_query)
        if not sanitized_query:
            await waiting_message_search.delete()
            await event.respond("So'rov noto'g'ri. Iltimos, boshqa matn kiriting.")
            return

        search_result = await SpotifyDownloader.search_spotify_based_on_user_input(sanitized_query)
        if len(search_result) == 0:
            await waiting_message_search.delete()
            await event.respond("Mos qo'shiq topilmadi.")
            return

        button_list = Buttons.get_search_result_buttons(sanitized_query, search_result)
        await event.respond(BotMessageHandler.search_result_message, buttons=button_list)
        await waiting_message_search.delete()

    @staticmethod
    async def handle_user_info_command(event):
        await update_bot_version_user_season(event)
        user_id = event.sender_id
        username = f"@{event.sender.username}" if event.sender.username else "mavjud emas"
        first_name = event.sender.first_name or "mavjud emas"
        last_name = event.sender.last_name or "mavjud emas"
        user_info_message = (
            f"👤 Foydalanuvchi ma'lumotlari\n\n"
            f"ID: {user_id}\n"
            f"Username: {username}\n"
            f"Ism: {first_name}\n"
            f"Familiya: {last_name}\n"
            f"Bot: {event.sender.bot}\n"
            f"Tasdiqlangan: {event.sender.verified}\n"
            f"Cheklangan: {event.sender.restricted}\n"
            f"Scam: {event.sender.scam}\n"
            f"Support: {event.sender.support}"
        )
        await event.reply(user_info_message)
