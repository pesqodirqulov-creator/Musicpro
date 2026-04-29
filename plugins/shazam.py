import logging
import os

from utils import Shazam

logger = logging.getLogger(__name__)


class ShazamHelper:
    @classmethod
    def initialize(cls):
        cls.Shazam = Shazam()
        cls.voice_repository_dir = "repository/Voices"
        os.makedirs(cls.voice_repository_dir, exist_ok=True)

    @staticmethod
    async def recognize(file_path):
        try:
            try:
                out = await ShazamHelper.Shazam.recognize(file_path)
            except Exception:
                out = await ShazamHelper.Shazam.recognize_song(file_path)
            return ShazamHelper.extract_song_details(out)
        except Exception as exc:
            logger.warning("Shazam aniqlash xatosi: %s", exc)
            return ""

    @staticmethod
    def extract_spotify_link(data):
        try:
            for provider in data['track']['hub']['providers']:
                if provider['type'] == 'SPOTIFY':
                    for action in provider['actions']:
                        if action['type'] == 'uri':
                            return action['uri']
        except Exception:
            return None
        return None

    @staticmethod
    def extract_song_details(data):
        try:
            music_name = data['track']['title']
            artists_name = data['track']['subtitle']
            return f"{music_name}, {artists_name}"
        except Exception:
            return ""
