from telethon.errors.rpcerrorlist import MessageNotModifiedError

from .glob_variables import BotState
from .buttons import Buttons
from utils import db, TweetCapture


class BotMessageHandler:
    start_message = (
        "Xush kelibsiz! 🎧\n\n"
        "Menga qo'shiq nomi, ijrochi nomi yoki havolani yuboring — men sizga kerakli faylni topishga yordam beraman.\n\n"
        "Qo'llanmani ko'rish uchun /help buyrug'ini yuboring yoki pastdagi tugmadan foydalaning."
    )

    instruction_message = (
        "📘 Botdan foydalanish yo'riqnomasi\n\n"
        "🎵 Musiqa qidirish:\n"
        "1. Qo'shiq yoki ijrochi nomini yuboring\n"
        "2. Natijalardan keraklisini tanlang\n"
        "3. Yuklab olish tugmalaridan foydalaning\n\n"
        "🔗 Havolalar bilan ishlash:\n"
        "• Spotify trek yoki playlist havolasi\n"
        "• YouTube video havolasi\n"
        "• Instagram post/reel havolasi\n"
        "• X/Twitter post havolasi\n\n"
        "🎤 Ovozli xabar:\n"
        "Qo'shiq parchasi yozilgan ovozli xabar yuborsangiz, bot qo'shiqni aniqlashga harakat qiladi.\n\n"
        "⚙️ /settings orqali sifat, yuklash usuli va boshqa sozlamalarni boshqarishingiz mumkin."
    )

    search_result_message = "🎵 So'rovingiz bo'yicha topilgan natijalar:"
    core_selection_message = "⚙️ Yuklab olish usulini tanlang"
    JOIN_CHANNEL_MESSAGE = "Davom etish uchun avval kerakli kanal(lar)ga qo'shiling."
    search_playlist_message = "Playlist ichidagi treklar:"

    @staticmethod
    async def send_message(event, text, buttons=None):
        await BotState.initialize_user_state(event.sender_id)
        await BotState.BOT_CLIENT.send_message(event.chat_id, text, buttons=buttons)

    @staticmethod
    async def edit_message(event, message_text, buttons=None):
        await BotState.initialize_user_state(event.sender_id)
        try:
            await event.edit(message_text, buttons=buttons)
        except MessageNotModifiedError:
            pass

    @staticmethod
    async def edit_quality_setting_message(event):
        music_quality = await db.get_user_music_quality(event.sender_id)
        if music_quality:
            message = (
                f"🎚 Joriy sifat sozlamasi:\n"
                f"Format: {music_quality['format']}\n"
                f"Sifat: {music_quality['quality']}\n\n"
                "Mavjud variantlar:"
            )
        else:
            message = "Sifat sozlamasi topilmadi."
        await BotMessageHandler.edit_message(event, message, buttons=Buttons.get_quality_setting_buttons(music_quality))

    @staticmethod
    async def edit_core_setting_message(event):
        downloading_core = await db.get_user_downloading_core(event.sender_id)
        if downloading_core:
            message = BotMessageHandler.core_selection_message + f"\n\nJoriy usul: {downloading_core}"
        else:
            message = BotMessageHandler.core_selection_message + "\n\nYuklash usuli topilmadi."
        await BotMessageHandler.edit_message(event, message, buttons=Buttons.get_core_setting_buttons(downloading_core))

    @staticmethod
    async def edit_subscription_status_message(event):
        is_subscribed = await db.is_user_subscribed(event.sender_id)
        holat = "faol" if is_subscribed else "o'chirilgan"
        message = f"📣 Obuna sozlamasi\n\nJoriy holat: {holat}"
        await BotMessageHandler.edit_message(event, message, buttons=Buttons.get_subscription_setting_buttons(is_subscribed))

    @staticmethod
    async def edit_tweet_capture_setting_message(event):
        night_mode = await TweetCapture.get_settings(event.sender_id)
        mode = night_mode.get("night_mode", "0")
        mode_to_show = {"0": "Yorug'", "1": "Qorong'i", "2": "Qora"}.get(mode, "Yorug'")
        message = f"🖼 X/Twitter skrinshot sozlamasi\n\nJoriy rejim: {mode_to_show}"
        await BotMessageHandler.edit_message(event, message, buttons=Buttons.get_tweet_capture_setting_buttons(mode))
