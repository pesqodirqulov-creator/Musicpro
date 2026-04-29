import hashlib
import logging
import os
import re

import aiohttp
import bs4
from telethon.tl.custom import Button

from run.glob_variables import BotState
from utils import TweetCapture, asyncio, db

logger = logging.getLogger(__name__)


class X:
    @classmethod
    def initialize(cls):
        cls.screen_shot_path = 'repository/ScreenShots'
        os.makedirs(cls.screen_shot_path, exist_ok=True)

    @staticmethod
    def get_screenshot_path(tweet_url):
        url_hash = hashlib.blake2b(tweet_url.encode()).hexdigest()
        return os.path.join(X.screen_shot_path, f"{url_hash}.png")

    @staticmethod
    async def take_screenshot_of_tweet(event, tweet_url):
        tweet_message = await event.respond("Post skrinshoti tayyorlanmoqda. Iltimos, biroz kuting...")
        settings = await TweetCapture.get_settings(event.sender_id)
        night_mode = settings.get('night_mode', '0')
        screenshot_path = X.get_screenshot_path(tweet_url + night_mode)
        try:
            if not os.path.exists(screenshot_path):
                await TweetCapture.screenshot(tweet_url, screenshot_path, night_mode)
            return screenshot_path
        except Exception as exc:
            await tweet_message.edit(f"Post skrinshotini olishda xatolik yuz berdi: {exc}")
            return None
        finally:
            try:
                await tweet_message.delete()
            except Exception:
                pass

    @staticmethod
    async def send_screenshot(client, event, tweet_url) -> bool:
        screenshot_path = await X.take_screenshot_of_tweet(event, tweet_url)
        if not screenshot_path:
            return False
        has_media = await X.has_media(tweet_url)
        screen_shot_message = await event.respond("Skrinshot yuborilmoqda...")
        button = Button.inline("Medianni yuklash", data=f"X/dl/{tweet_url.replace('https://x.com/', '').replace('https://twitter.com/', '')}") if has_media else None
        try:
            await client.send_file(event.chat_id, screenshot_path, caption="Mana, siz so'ragan post skrinshoti.", buttons=button)
            return True
        except Exception as exc:
            await screen_shot_message.edit(f"Skrinshot yuborilmadi: {exc}")
            return False
        finally:
            try:
                await screen_shot_message.delete()
            except Exception:
                pass

    @staticmethod
    def contains_x_or_twitter_link(text):
        pattern = r'(https?://(?:www\.)?twitter\.com/[^/\s]+/status/\d+|https?://(?:www\.)?x\.com/[^/\s]+(?:/status/\d+)?)'
        return bool(re.search(pattern, text or ""))

    @staticmethod
    def find_and_return_x_or_twitter_link(text):
        pattern = r'(https?://(?:www\.)?twitter\.com/[^/\s]+/status/\d+|https?://(?:www\.)?x\.com/[^?\s]+)'
        match = re.search(pattern, text or "")
        return match.group(0) if match else None

    @staticmethod
    def normalize_url(link):
        if "x.com" in link:
            return link.replace("x.com", "fxtwitter.com")
        if "twitter.com" in link:
            return link.replace("twitter.com", "fxtwitter.com")
        return link

    @staticmethod
    async def has_media(link):
        normalized_link = X.normalize_url(link)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(normalized_link) as response:
                    if response.status != 200:
                        return False
                    html = await response.text()
                    soup = bs4.BeautifulSoup(html, "lxml")
                    return soup.find("meta", attrs={"property": "og:video"}) is not None or soup.find("meta", attrs={"property": "og:image"}) is not None
        except Exception as exc:
            logger.warning("Media tekshiruvida xatolik: %s", exc)
            return False

    @staticmethod
    async def fetch_media_url(link):
        normalized_link = X.normalize_url(link)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(normalized_link) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                    soup = bs4.BeautifulSoup(html, "lxml")
                    meta_tag = soup.find("meta", attrs={"property": "og:video"}) or soup.find("meta", attrs={"property": "og:image"})
                    return meta_tag['content'] if meta_tag else None
        except Exception as exc:
            logger.warning("Media URL ni olishda xatolik: %s", exc)
            return None

    @staticmethod
    async def download(client, event):
        query_data = f"{event.data}"
        link = "https://x.com/" + query_data.split("X/dl/")[-1][:-1]
        media_url = await X.fetch_media_url(link)
        if not media_url:
            await event.reply("Media topilmadi yoki havola yaroqsiz.")
            return
        upload_message = await event.reply("Media yuklanmoqda...")
        try:
            await client.send_file(event.chat_id, media_url, caption="Mana, siz so'ragan media.")
        except Exception as exc:
            logger.warning("X media yuborilmadi: %s", exc)
            await event.reply("Media yuborilmadi. Havolani qayta tekshirib ko'ring.")
        finally:
            try:
                await upload_message.delete()
            except Exception:
                pass
