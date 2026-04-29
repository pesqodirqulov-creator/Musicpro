import hashlib
import logging
import os
import re

from telethon.tl.custom import Button
from telethon.tl.types import InputMediaPhotoExternal
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from run.buttons import Buttons
from utils import WebpageMediaEmptyError, db

logger = logging.getLogger(__name__)


class YoutubeDownloader:
    @classmethod
    def initialize(cls):
        cls.MAXIMUM_DOWNLOAD_SIZE_MB = 100
        cls.DOWNLOAD_DIR = 'repository/Youtube'
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)

    @staticmethod
    def get_file_path(url, format_id, extension):
        url_hash = hashlib.blake2b(f"{url}|{format_id}|{extension}".encode()).hexdigest()
        return os.path.join(YoutubeDownloader.DOWNLOAD_DIR, f"{url_hash}.{extension}")

    @staticmethod
    def is_youtube_link(url):
        youtube_patterns = [
            r'(https?\:\/\/)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11}).*',
            r'(https?\:\/\/)?www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/v\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/[^\/]+\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
        ]
        return any(re.match(pattern, url or "") for pattern in youtube_patterns)

    @staticmethod
    def extract_youtube_url(text):
        youtube_patterns = [
            r'(https?\:\/\/)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11}).*',
            r'(https?\:\/\/)?www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/v\/([a-zA-Z0-9_-]{11})(?!.*list=)',
            r'(https?\:\/\/)?www\.youtube\.com\/[^\/]+\?v=([a-zA-Z0-9_-]{11})(?!.*list=)',
        ]
        for pattern in youtube_patterns:
            match = re.search(pattern, text or "")
            if match:
                video_id = match.group(2)
                if 'youtube.com/shorts/' in match.group(0):
                    return f'https://www.youtube.com/shorts/{video_id}'
                return f'https://www.youtube.com/watch?v={video_id}'
        return None

    @staticmethod
    def _extract_info(url, download=False, **extra):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            **extra,
        }
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=download)

    @staticmethod
    async def send_youtube_info(client, event, youtube_link):
        url = youtube_link
        video_id = youtube_link.split("?si=")[0].replace("https://www.youtube.com/watch?v=", "").replace("https://www.youtube.com/shorts/", "")
        info = YoutubeDownloader._extract_info(url, download=False)
        formats = info.get('formats', [])
        thumbnail_url = info.get('thumbnail')
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']

        buttons = []
        for group in (video_formats, audio_formats):
            counter = 0
            for fmt in reversed(group):
                extension = fmt.get('ext')
                resolution = fmt.get('resolution') or fmt.get('format_note') or 'audio'
                filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                if not extension or not filesize or counter >= 5:
                    continue
                filesize_mb = f"{filesize / 1024 / 1024:.2f}MB"
                button_data = f"yt/dl/{video_id}/{extension}/{fmt['format_id']}/{filesize_mb}"
                label = f"{extension.upper()} - {resolution} - {filesize_mb}"
                button = [Button.inline(label, data=button_data)]
                if button not in buttons:
                    buttons.append(button)
                    counter += 1
        buttons.append(Buttons.cancel_button)

        caption = "📺 Yuklab olish uchun formatni tanlang:"
        if thumbnail_url:
            try:
                thumbnail = InputMediaPhotoExternal(thumbnail_url)
                thumbnail.ttl_seconds = 0
                await client.send_file(event.chat_id, file=thumbnail, caption=caption, buttons=buttons)
                return
            except WebpageMediaEmptyError:
                pass
        await event.respond(caption, buttons=buttons)

    @staticmethod
    async def download_and_send_yt_file(client, event):
        user_id = event.sender_id
        if await db.get_file_processing_flag(user_id):
            await event.respond("Siz uchun boshqa fayl hali qayta ishlanmoqda. Biroz kuting.")
            return

        data = event.data.decode('utf-8')
        parts = data.split('/')
        if len(parts) != 6:
            await event.answer("Tugma ma'lumoti yaroqsiz.", alert=True)
            return

        _, _, video_id, extension, format_id, filesize = parts
        size_mb = float(filesize.replace("MB", ""))
        if size_mb > YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB:
            await event.answer(f"Fayl hajmi {YoutubeDownloader.MAXIMUM_DOWNLOAD_SIZE_MB}MB dan katta.", alert=True)
            return

        await db.set_file_processing_flag(user_id, True)
        url = "https://www.youtube.com/watch?v=" + video_id
        path = YoutubeDownloader.get_file_path(url, format_id, extension)
        local_message = None
        try:
            if not os.path.isfile(path):
                downloading_message = await event.respond("YouTube fayli yuklab olinmoqda...")
                info = YoutubeDownloader._extract_info(url, download=True, format=format_id, outtmpl=path)
                duration = info.get('duration', 0)
                await downloading_message.delete()
            else:
                local_message = await event.respond("Fayl keshda topildi, tezkor yuborish tayyorlanmoqda...")
                info = YoutubeDownloader._extract_info(url, download=False, format=format_id)
                duration = info.get('duration', 0)

            upload_message = await event.respond("Fayl yuborilmoqda...")
            caption = f"Marhamat!\nYouTube ID: {video_id}\nDavomiylik: {duration} soniya"
            await client.send_file(
                event.chat_id,
                path,
                caption=caption,
                supports_streaming=extension == "mp4",
                force_document=False,
            )
            await upload_message.delete()
        except DownloadError as exc:
            await event.respond(f"YouTube faylini yuklab bo'lmadi: {exc}")
        except Exception as exc:
            logger.exception("YouTube yuklash xatosi")
            await event.respond(f"So'rovni bajarishda xatolik yuz berdi: {exc}")
        finally:
            if local_message:
                try:
                    await local_message.delete()
                except Exception:
                    pass
            await db.set_file_processing_flag(user_id, False)
