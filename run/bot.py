import logging

from telethon import events
from telethon.tl.types import MessageMediaDocument

from plugins.instagram import Insta
from plugins.shazam import ShazamHelper
from plugins.spotify import SpotifyDownloader
from plugins.x import X
from plugins.youtube import YoutubeDownloader
from run.buttons import Buttons
from run.channel_checker import handle_continue_in_membership_message, is_user_in_channel, respond_based_on_channel_membership
from run.commands import BotCommandHandler
from run.glob_variables import BotState
from run.messages import BotMessageHandler
from run.version_checker import update_bot_version_user_season
from utils import BroadcastManager, TweetCapture, asyncio, db, sanitize_query

logger = logging.getLogger(__name__)


class Bot:
    Client = None

    @staticmethod
    async def initialize():
        """Bot ishga tushishidan oldin modullarni tayyorlaydi."""
        await db.initialize_database()
        await db.reset_all_file_processing_flags()

        for initializer in (
            ("Spotify", SpotifyDownloader.initialize),
            ("Shazam", ShazamHelper.initialize),
            ("X/Twitter", X.initialize),
            ("Instagram", Insta.initialize),
            ("YouTube", YoutubeDownloader.initialize),
        ):
            name, func = initializer
            try:
                result = func()
                if asyncio.iscoroutine(result):
                    await result
                logger.info("%s moduli tayyorlandi", name)
            except Exception as exc:
                logger.exception("%s moduli ishga tushmadi: %s", name, exc)

        Bot.initialize_messages()
        Bot.initialize_buttons()
        await Bot.initialize_action_queries()
        logger.info("Bot to'liq ishga tushirishga tayyor")

    @classmethod
    def initialize_messages(cls):
        cls.start_message = BotMessageHandler.start_message
        cls.instruction_message = BotMessageHandler.instruction_message
        cls.search_result_message = BotMessageHandler.search_result_message
        cls.core_selection_message = BotMessageHandler.core_selection_message
        cls.JOIN_CHANNEL_MESSAGE = BotMessageHandler.JOIN_CHANNEL_MESSAGE
        cls.search_playlist_message = BotMessageHandler.search_playlist_message

    @classmethod
    def initialize_buttons(cls):
        cls.main_menu_buttons = Buttons.main_menu_buttons
        cls.back_button = Buttons.back_button
        cls.setting_button = Buttons.setting_button
        cls.back_button_to_setting = Buttons.back_button_to_setting
        cls.cancel_broadcast_button = Buttons.cancel_broadcast_button
        cls.admins_buttons = Buttons.admins_buttons
        cls.broadcast_options_buttons = Buttons.broadcast_options_buttons

    @classmethod
    async def initialize_action_queries(cls):
        cls.button_actions = {
            b"membership/continue": lambda e: asyncio.create_task(handle_continue_in_membership_message(e)),
            b"instructions": lambda e: asyncio.create_task(BotMessageHandler.edit_message(e, Bot.instruction_message, buttons=Bot.back_button)),
            b"back": lambda e: asyncio.create_task(BotMessageHandler.edit_message(e, f"Salom, {e.sender.first_name or 'do\'st'}! 👋\n{Bot.start_message}", buttons=Bot.main_menu_buttons)),
            b"setting": lambda e: asyncio.create_task(BotMessageHandler.edit_message(e, "⚙️ Sozlamalar", buttons=Bot.setting_button)),
            b"setting/back": lambda e: asyncio.create_task(BotMessageHandler.edit_message(e, "⚙️ Sozlamalar", buttons=Bot.setting_button)),
            b"setting/quality": lambda e: asyncio.create_task(BotMessageHandler.edit_quality_setting_message(e)),
            b"setting/quality/mp3/320": lambda e: asyncio.create_task(Bot.change_music_quality(e, "mp3", "320")),
            b"setting/quality/mp3/128": lambda e: asyncio.create_task(Bot.change_music_quality(e, "mp3", "128")),
            b"setting/quality/flac": lambda e: asyncio.create_task(Bot.change_music_quality(e, "flac", "693")),
            b"setting/core": lambda e: asyncio.create_task(BotMessageHandler.edit_core_setting_message(e)),
            b"setting/core/auto": lambda e: asyncio.create_task(Bot.change_downloading_core(e, "Auto")),
            b"setting/core/spotdl": lambda e: asyncio.create_task(Bot.change_downloading_core(e, "SpotDL")),
            b"setting/core/youtubedl": lambda e: asyncio.create_task(Bot.change_downloading_core(e, "YoutubeDL")),
            b"setting/subscription": lambda e: asyncio.create_task(BotMessageHandler.edit_subscription_status_message(e)),
            b"setting/subscription/cancel": lambda e: asyncio.create_task(Bot.cancel_subscription(e)),
            b"setting/subscription/cancel/quite": lambda e: asyncio.create_task(Bot.cancel_subscription(e, quite=True)),
            b"setting/subscription/add": lambda e: asyncio.create_task(Bot.add_subscription(e)),
            b"setting/TweetCapture": lambda e: asyncio.create_task(BotMessageHandler.edit_tweet_capture_setting_message(e)),
            b"setting/TweetCapture/mode/0": lambda e: asyncio.create_task(Bot.change_tweet_capture_night_mode(e, "0")),
            b"setting/TweetCapture/mode/1": lambda e: asyncio.create_task(Bot.change_tweet_capture_night_mode(e, "1")),
            b"setting/TweetCapture/mode/2": lambda e: asyncio.create_task(Bot.change_tweet_capture_night_mode(e, "2")),
            b"cancel": lambda e: e.delete(),
            b"admin/cancel_broadcast": lambda e: asyncio.create_task(BotState.set_admin_broadcast(e.sender_id, False)),
            b"admin/stats": lambda e: asyncio.create_task(BotCommandHandler.handle_stats_command(e)),
            b"admin/broadcast": lambda e: asyncio.create_task(BotMessageHandler.edit_message(e, "📣 Ommaviy yuborish turi", buttons=Bot.broadcast_options_buttons)),
            b"admin/broadcast/all": lambda e: asyncio.create_task(Bot.handle_broadcast(e, send_to_all=True)),
            b"admin/broadcast/subs": lambda e: asyncio.create_task(Bot.handle_broadcast(e, send_to_subs=True)),
            b"admin/broadcast/specified": lambda e: asyncio.create_task(Bot.handle_broadcast(e, send_to_specified=True)),
            b"unavailable_feature": lambda e: asyncio.create_task(Bot.handle_unavailable_feature(e)),
        }

    @staticmethod
    async def change_music_quality(event, music_format, quality):
        user_id = event.sender_id
        music_quality = {"format": music_format, "quality": quality}
        await db.set_user_music_quality(user_id, music_quality)
        await BotMessageHandler.edit_message(
            event,
            f"✅ Sifat yangilandi.\n\nFormat: {music_quality['format']}\nSifat: {music_quality['quality']}",
            buttons=Buttons.get_quality_setting_buttons(music_quality),
        )

    @staticmethod
    async def change_downloading_core(event, downloading_core):
        user_id = event.sender_id
        await db.set_user_downloading_core(user_id, downloading_core)
        await BotMessageHandler.edit_message(
            event,
            f"✅ Yuklash usuli yangilandi.\n\nJoriy usul: {downloading_core}",
            buttons=Buttons.get_core_setting_buttons(downloading_core),
        )

    @staticmethod
    async def change_tweet_capture_night_mode(event, mode: str):
        user_id = event.sender_id
        await TweetCapture.set_settings(user_id, {"night_mode": mode})
        mode_to_show = {"0": "Yorug'", "1": "Qorong'i", "2": "Qora"}.get(mode, "Yorug'")
        await BotMessageHandler.edit_message(
            event,
            f"✅ Ko'rinish yangilandi.\n\nJoriy rejim: {mode_to_show}",
            buttons=Buttons.get_tweet_capture_setting_buttons(mode),
        )

    @staticmethod
    async def cancel_subscription(event, quite: bool = False):
        user_id = event.sender_id
        if await db.is_user_subscribed(user_id):
            await db.remove_subscribed_user(user_id)
            if not quite:
                await BotMessageHandler.edit_message(event, "✅ Obuna bekor qilindi.", buttons=Buttons.get_subscription_setting_buttons(False))
            else:
                await event.respond("✅ Obuna bekor qilindi. Istalgan payt /subscribe buyrug'i orqali qayta yoqishingiz mumkin.")

    @staticmethod
    async def add_subscription(event):
        user_id = event.sender_id
        if not await db.is_user_subscribed(user_id):
            await db.add_subscribed_user(user_id)
            await BotMessageHandler.edit_message(event, "✅ Obuna faollashtirildi.", buttons=Buttons.get_subscription_setting_buttons(True))

    @staticmethod
    async def process_bot_interaction(event) -> bool:
        user_id = event.sender_id
        await update_bot_version_user_season(event)
        if not await db.get_user_updated_flag(user_id):
            return False

        channels_user_is_not_in = await is_user_in_channel(user_id)
        if channels_user_is_not_in and user_id not in BotState.ADMIN_USER_IDS:
            return await respond_based_on_channel_membership(event, None, None, channels_user_is_not_in)

        if await BotState.get_admin_broadcast(user_id):
            await BotState.set_admin_message_to_send(user_id, event.message)
            return False
        return True

    @staticmethod
    async def handle_broadcast(event, send_to_all: bool = False, send_to_subs: bool = False, send_to_specified: bool = False):
        user_id = event.sender_id
        if user_id not in BotState.ADMIN_USER_IDS:
            return

        if send_to_specified:
            await BotState.set_send_to_specified_flag(user_id, True)

        await BotState.set_admin_broadcast(user_id, True)
        if send_to_all:
            await BroadcastManager.add_all_users_to_temp()
        elif send_to_specified:
            await BroadcastManager.remove_all_users_from_temp()
            timer_message = await event.respond("60 soniya ichida foydalanuvchi ID larini vergul bilan yuboring.", buttons=Bot.cancel_broadcast_button)
            for remaining_time in range(59, 0, -1):
                await timer_message.edit(f"ID yuborish uchun {remaining_time} soniya qoldi.")
                if not await BotState.get_admin_broadcast(user_id):
                    await timer_message.edit("Yuborish bekor qilindi.", buttons=None)
                    await BotState.set_send_to_specified_flag(user_id, False)
                    await BotState.set_admin_message_to_send(user_id, None)
                    return
                if await BotState.get_admin_message_to_send(user_id) is not None:
                    break
                await asyncio.sleep(1)
            await BotState.set_send_to_specified_flag(user_id, False)
            try:
                parts = await BotState.get_admin_message_to_send(user_id)
                user_ids = [int(part) for part in parts.message.replace(" ", "").split(",") if part]
                for target_id in user_ids:
                    await BroadcastManager.add_user_to_temp(target_id)
            except Exception:
                await timer_message.edit("ID formati noto'g'ri. Namuna: 12345,67890")
                await BotState.set_admin_message_to_send(user_id, None)
                await BotState.set_admin_broadcast(user_id, False)
                return
            await BotState.set_admin_message_to_send(user_id, None)

        time_to_send = await event.respond("60 soniya ichida yuboriladigan xabarni jo'nating.", buttons=Bot.cancel_broadcast_button)
        for remaining_time in range(59, 0, -1):
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
            await BroadcastManager.remove_all_users_from_temp()
            return

        try:
            message_to_send = await BotState.get_admin_message_to_send(user_id)
            if await BotState.get_admin_broadcast(user_id) and send_to_specified:
                await BroadcastManager.broadcast_message_to_temp_members(Bot.Client, message_to_send)
            elif await BotState.get_admin_broadcast(user_id) and send_to_subs:
                await BroadcastManager.broadcast_message_to_sub_members(Bot.Client, message_to_send, Buttons.cancel_subscription_button_quite)
            elif await BotState.get_admin_broadcast(user_id) and send_to_all:
                await BroadcastManager.broadcast_message_to_temp_members(Bot.Client, message_to_send)
            await event.respond("📣 Ommaviy yuborish boshlandi.")
        except Exception as exc:
            await event.respond(f"Ommaviy yuborishda xatolik: {exc}")
        finally:
            await BroadcastManager.remove_all_users_from_temp()
            await BotState.set_admin_broadcast(user_id, False)
            await BotState.set_admin_message_to_send(user_id, None)

    @staticmethod
    async def process_audio_file(event, user_id):
        if not await Bot.process_bot_interaction(event):
            return

        waiting_message = await event.respond("⏳")
        process_file_message = await event.respond("Ovozli fayl tahlil qilinmoqda...")
        try:
            file_path = await event.message.download_media(file=ShazamHelper.voice_repository_dir)
            shazam_recognized = await ShazamHelper.recognize(file_path)
            if not shazam_recognized:
                await event.respond("Qo'shiqni aniqlab bo'lmadi. Iltimos, aniqroq parchani yuboring.")
                return

            sanitized_query = await sanitize_query(shazam_recognized)
            if not sanitized_query:
                await event.respond("Aniqlangan matn yaroqsiz bo'ldi. Qayta urinib ko'ring.")
                return

            search_result = await SpotifyDownloader.search_spotify_based_on_user_input(sanitized_query, limit=10)
            button_list = Buttons.get_search_result_buttons(sanitized_query, search_result)
            await event.respond(Bot.search_result_message, buttons=button_list)
        except Exception as exc:
            logger.exception("Ovozli xabarni qayta ishlash xatosi")
            await event.respond(f"Ovozli xabarni qayta ishlashda xatolik yuz berdi: {exc}")
        finally:
            await waiting_message.delete()
            await process_file_message.delete()

    @staticmethod
    async def process_spotify_link(event):
        if not await Bot.process_bot_interaction(event):
            return
        waiting_message = await event.respond("⏳")
        try:
            info_tuple = await SpotifyDownloader.download_and_send_spotify_info(event, is_query=False)
            if not info_tuple:
                await event.respond("Spotify havolasi qayta ishlanmadi.")
        finally:
            await waiting_message.delete()

    @staticmethod
    async def process_text_query(event):
        if not await Bot.process_bot_interaction(event):
            return

        text = (event.message.text or "").strip()
        if len(text) > 100:
            await event.respond("Qidiruv matni juda uzun. Iltimos, qisqaroq matn yuboring.")
            return

        waiting_message_search = await event.respond('⏳')
        try:
            sanitized_query = await sanitize_query(text)
            if not sanitized_query:
                await event.respond("So'rov yaroqsiz. Iltimos, boshqa matn kiriting.")
                return

            search_result = await SpotifyDownloader.search_spotify_based_on_user_input(sanitized_query, limit=10)
            button_list = Buttons.get_search_result_buttons(sanitized_query, search_result)
            await event.respond(Bot.search_result_message, buttons=button_list)
        except Exception as exc:
            logger.exception("Matnli qidiruv xatosi")
            await event.respond(f"Qidiruvda xatolik yuz berdi: {exc}")
        finally:
            await waiting_message_search.delete()

    @staticmethod
    async def handle_next_prev_page(event):
        query_data = str(event.data)
        is_playlist = query_data.split("/")[1] == "p"
        current_page = query_data.split("/page/")[-1][:-1]
        search_query = query_data.split("/")[2]

        if current_page == "0":
            return await event.answer("Bu sahifa mavjud emas.", alert=True)

        if is_playlist:
            search_result = await SpotifyDownloader.get_playlist_tracks(search_query, limit=int(current_page) * 10)
            button_list = Buttons.get_playlist_search_buttons(search_query, search_result, page=int(current_page))
        else:
            search_result = await SpotifyDownloader.search_spotify_based_on_user_input(search_query, limit=int(current_page) * 10)
            button_list = Buttons.get_search_result_buttons(search_query, search_result, page=int(current_page))

        try:
            await event.edit(buttons=button_list)
        except Exception:
            await event.answer("Sahifani almashtirib bo'lmadi.", alert=True)

    @staticmethod
    async def process_x_or_twitter_link(event):
        if not await Bot.process_bot_interaction(event):
            return
        x_link = X.find_and_return_x_or_twitter_link(event.message.text)
        if x_link:
            return await X.send_screenshot(Bot.Client, event, x_link)

    @staticmethod
    async def process_youtube_link(event):
        if not await Bot.process_bot_interaction(event):
            return
        waiting_message = await event.respond('⏳')
        try:
            youtube_link = YoutubeDownloader.extract_youtube_url(event.message.text)
            if not youtube_link:
                await event.respond("YouTube havolasi noto'g'ri.")
                return
            await YoutubeDownloader.send_youtube_info(Bot.Client, event, youtube_link)
        finally:
            await waiting_message.delete()

    @staticmethod
    async def handle_unavailable_feature(event):
        await event.answer("Bu funksiya hozircha mavjud emas.", alert=True)

    @staticmethod
    async def search_inside_playlist(event):
        query_data = str(event.data)
        playlist_id = query_data.split("/playlist/")[-1][:-1]
        waiting_message = await event.respond('⏳')
        try:
            search_result = await SpotifyDownloader.get_playlist_tracks(playlist_id)
            button_list = Buttons.get_playlist_search_buttons(playlist_id, search_result)
            await event.respond(Bot.search_result_message, buttons=button_list)
        except Exception as exc:
            await event.respond(f"Playlist ichida qidirishda xatolik: {exc}")
        finally:
            await waiting_message.delete()

    @staticmethod
    async def handle_spotify_callback(event):
        handlers = {
            "spotify/dl/icon/": SpotifyDownloader.send_music_icon,
            "spotify/dl/30s_preview": SpotifyDownloader.send_30s_preview,
            "spotify/artist/": SpotifyDownloader.send_artists_info,
            "spotify/lyrics": SpotifyDownloader.send_music_lyrics,
            "spotify/dl/playlist/": SpotifyDownloader.download_spotify_file_and_send,
            "spotify/s/playlist/": Bot.search_inside_playlist,
            "spotify/dl/music/": SpotifyDownloader.download_spotify_file_and_send,
            "spotify/info/": SpotifyDownloader.download_and_send_spotify_info,
        }
        for key, handler in handlers.items():
            if event.data.startswith(key.encode()):
                await handler(event)
                return

    @staticmethod
    async def handle_youtube_callback(client, event):
        if event.data.startswith(b"yt/dl/"):
            await YoutubeDownloader.download_and_send_yt_file(client, event)

    @staticmethod
    async def handle_x_callback(client, event):
        if event.data.startswith(b"X/dl"):
            await X.download(client, event)

    @staticmethod
    async def callback_query_handler(event):
        user_id = event.sender_id
        await update_bot_version_user_season(event)
        if not await db.get_user_updated_flag(user_id):
            return

        action = Bot.button_actions.get(event.data)
        if action:
            await action(event)
        elif event.data.startswith(b"spotify"):
            await Bot.handle_spotify_callback(event)
        elif event.data.startswith(b"yt"):
            await Bot.handle_youtube_callback(Bot.Client, event)
        elif event.data.startswith(b"X"):
            await Bot.handle_x_callback(Bot.Client, event)
        elif event.data.startswith(b"next_page") or event.data.startswith(b"prev_page"):
            await Bot.handle_next_prev_page(event)

    @staticmethod
    async def handle_message(event):
        user_id = event.sender_id
        text = event.message.text or ""
        try:
            if isinstance(event.message.media, MessageMediaDocument):
                if getattr(event.message.media, "voice", False) or getattr(event.message, "voice", False):
                    await Bot.process_audio_file(event, user_id)
                else:
                    await event.respond("Men hozircha faqat matn, havola va ovozli xabarlarni qayta ishlay olaman.")
            elif text and YoutubeDownloader.is_youtube_link(text):
                await Bot.process_youtube_link(event)
            elif text and SpotifyDownloader.is_spotify_link(text):
                await Bot.process_spotify_link(event)
            elif text and X.contains_x_or_twitter_link(text):
                await Bot.process_x_or_twitter_link(event)
            elif text and Insta.is_instagram_url(text):
                await Insta.download(Bot.Client, event)
            elif text and not text.startswith('/'):
                await Bot.process_text_query(event)
        except Exception as exc:
            logger.exception("Xabarni qayta ishlashda xatolik")
            await event.respond(f"Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.\nSabab: {exc}")

    @staticmethod
    async def run():
        client = BotState.ensure_client()
        Bot.Client = await client.start(bot_token=BotState.BOT_TOKEN)
        Bot.Client.add_event_handler(BotCommandHandler.start, events.NewMessage(pattern=r'^/start$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_broadcast_command, events.NewMessage(pattern=r'^/broadcast(?:\s|$)|^/broadcast_to_all$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_settings_command, events.NewMessage(pattern=r'^/settings$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_subscribe_command, events.NewMessage(pattern=r'^/subscribe$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_unsubscribe_command, events.NewMessage(pattern=r'^/unsubscribe$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_help_command, events.NewMessage(pattern=r'^/help$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_quality_command, events.NewMessage(pattern=r'^/quality$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_core_command, events.NewMessage(pattern=r'^/core$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_admin_command, events.NewMessage(pattern=r'^/admin$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_stats_command, events.NewMessage(pattern=r'^/stats$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_ping_command, events.NewMessage(pattern=r'^/ping$'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_search_command, events.NewMessage(pattern=r'^/search'))
        Bot.Client.add_event_handler(BotCommandHandler.handle_user_info_command, events.NewMessage(pattern=r'^/user_info$'))
        Bot.Client.add_event_handler(Bot.callback_query_handler, events.CallbackQuery)
        Bot.Client.add_event_handler(Bot.handle_message, events.NewMessage)
        logger.info("Bot ishga tushdi")
        await Bot.Client.run_until_disconnected()
