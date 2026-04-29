"""Tweet/X postlarini suratga olish moduli."""

import logging
import os
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .database import db

logger = logging.getLogger(__name__)


class TweetCapture:
    @staticmethod
    def _chrome_options() -> Options:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--window-size=1280,2200")
        binary = os.getenv("GOOGLE_CHROME_BIN") or os.getenv("CHROME_BIN")
        if binary:
            options.binary_location = binary
        return options

    @staticmethod
    def _chrome_service() -> Service:
        driver_path = os.getenv("CHROMEDRIVER_PATH") or shutil.which("chromedriver")
        if not driver_path:
            driver_path = ChromeDriverManager().install()
        return Service(driver_path)

    @staticmethod
    def _create_driver():
        return webdriver.Chrome(service=TweetCapture._chrome_service(), options=TweetCapture._chrome_options())

    @staticmethod
    async def get_settings(user_id):
        return await db.get_user_tweet_capture_settings(user_id)

    @staticmethod
    async def set_settings(user_id, settings: dict):
        return await db.set_user_tweet_capture_settings(user_id, settings)

    @staticmethod
    def _normalize_url(tweet_url: str) -> str:
        return tweet_url.replace("x.com", "fxtwitter.com").replace("twitter.com", "fxtwitter.com")

    @staticmethod
    async def screenshot(tweet_url: str, screenshot_path: str, night_mode: str = "0") -> None:
        screenshot_path = str(Path(screenshot_path))
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        driver = None
        try:
            driver = TweetCapture._create_driver()
            url = TweetCapture._normalize_url(tweet_url)
            driver.get(url)
            try:
                driver.add_cookie({"name": "night_mode", "value": night_mode or "0"})
                driver.get(url)
            except Exception:
                logger.debug("night_mode cookieni qo'yib bo'lmadi")

            wait = WebDriverWait(driver, 20)
            article = wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            driver.execute_script("arguments[0].scrollIntoView(true);", article)
            article.screenshot(screenshot_path)
        except TimeoutException as exc:
            raise Exception("Postni topib bo'lmadi yoki sahifa juda sekin yuklandi.") from exc
        except WebDriverException as exc:
            logger.exception("TweetCapture xatosi")
            raise Exception("Brauzer ishga tushmadi. Railway uchun Chromium o'rnatilganini tekshiring.") from exc
        finally:
            if driver:
                driver.quit()
