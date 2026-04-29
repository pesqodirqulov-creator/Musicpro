import asyncio
import logging
import os
import re

import bs4
import requests
import wget

logger = logging.getLogger(__name__)


class Insta:
    @classmethod
    def initialize(cls):
        cls.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://saveig.app",
            "Referer": "https://saveig.app/en",
        }
        cls.download_dir = "repository/Instagram"
        os.makedirs(cls.download_dir, exist_ok=True)

    @staticmethod
    def is_instagram_url(text) -> bool:
        pattern = r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)(?:\/(?:p|reel|tv|stories)\/(?:[^\s\/]+)|\/([\w-]+)(?:\/(?:[^\s\/]+))?)'
        return bool(re.search(pattern, text or ""))

    @staticmethod
    def extract_url(text) -> str | None:
        pattern = r'(https?:\/\/(?:www\.)?(?:ddinstagram\.com|instagram\.com|instagr\.am)\/(?:p|reel|tv|stories)\/[\w-]+\/?(?:\?[^\s]+)?)'
        match = re.search(pattern, text or "")
        return match.group(0) if match else None

    @staticmethod
    def determine_content_type(text) -> str | None:
        for pattern, content_type in {
            '/p/': 'post',
            '/reel/': 'reel',
            '/tv': 'igtv',
            '/stories/': 'story',
        }.items():
            if pattern in text:
                return content_type
        return None

    @staticmethod
    async def download_content(client, event, start_message, link) -> bool:
        content_type = Insta.determine_content_type(link)
        try:
            if content_type == 'reel':
                await Insta.download_reel(client, event, link)
            elif content_type == 'post':
                await Insta.download_post(client, event, link)
            elif content_type == 'story':
                await Insta.download_story(client, event, link)
            else:
                await event.reply("Instagram kontentini topib bo'lmadi. Havola ochiq ekanini tekshiring.")
            return True
        except Exception as exc:
            logger.exception("Instagram yuklash xatosi")
            await event.reply(f"Instagram kontentini yuklashda xatolik yuz berdi: {exc}")
            return False
        finally:
            await start_message.delete()

    @staticmethod
    async def download(client, event) -> bool:
        link = Insta.extract_url(event.message.text)
        if not link:
            await event.respond("Instagram havolasi noto'g'ri ko'rinishda yuborildi.")
            return False
        start_message = await event.respond("Instagram havolasi qayta ishlanmoqda...")
        try:
            if "ddinstagram.com" not in link:
                link = link.replace("instagram.com", "ddinstagram.com")
            return await Insta.download_content(client, event, start_message, link)
        except Exception:
            return await Insta.download_content(client, event, start_message, link)

    @staticmethod
    async def download_reel(client, event, link):
        content_value = None
        try:
            meta_tag = await Insta.get_meta_tag(link)
            if meta_tag:
                content_value = f"https://ddinstagram.com{meta_tag['content']}"
        except Exception:
            content_value = None
        if not content_value:
            meta_tag = await Insta.search_saveig(link)
            content_value = meta_tag[0] if meta_tag else None
        if content_value:
            await Insta.send_file(client, event, content_value)
        else:
            await event.reply("Kontent topilmadi yoki vaqtincha mavjud emas.")

    @staticmethod
    async def download_post(client, event, link):
        meta_tags = await Insta.search_saveig(link)
        if not meta_tags:
            await event.reply("Post fayllarini topib bo'lmadi.")
            return
        for meta in meta_tags[:-1] if len(meta_tags) > 1 else meta_tags:
            await asyncio.sleep(1)
            await Insta.send_file(client, event, meta)

    @staticmethod
    async def download_story(client, event, link):
        meta_tag = await Insta.search_saveig(link)
        if meta_tag:
            await Insta.send_file(client, event, meta_tag[0])
        else:
            await event.reply("Story faylini topib bo'lmadi.")

    @staticmethod
    async def get_meta_tag(link):
        html = await asyncio.to_thread(lambda: requests.get(link, timeout=20).text)
        soup = bs4.BeautifulSoup(html, 'html.parser')
        return soup.find('meta', attrs={'property': 'og:video'})

    @staticmethod
    async def search_saveig(link):
        def _request():
            return requests.post(
                "https://saveig.app/api/ajaxSearch",
                data={"q": link, "t": "media", "lang": "en"},
                headers=Insta.headers,
                timeout=30,
            )

        response = await asyncio.to_thread(_request)
        if response.ok:
            res = response.json()
            return re.findall(r'href="(https?://[^"]+)"', res.get('data', ''))
        return None

    @staticmethod
    async def send_file(client, event, content_value):
        try:
            await client.send_file(event.chat_id, content_value, caption="Mana, siz so'ragan Instagram fayli.")
        except Exception:
            local_path = os.path.join(Insta.download_dir, os.path.basename(str(content_value).split('?')[0]))
            await asyncio.to_thread(wget.download, content_value, local_path)
            await client.send_file(event.chat_id, local_path, caption="Mana, siz so'ragan Instagram fayli.")
