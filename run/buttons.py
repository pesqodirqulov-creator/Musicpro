from telethon.tl.custom import Button


class Buttons:
    source_code_button = [
        Button.url("Manba kodi", url="https://github.com/AdibNikjou/MusicDownloader-Telegram-Bot")
    ]

    main_menu_buttons = [
        [Button.inline("Yo'riqnoma", b"instructions"), Button.inline("Sozlamalar", b"setting")],
        source_code_button,
        [Button.url("Muallif bilan bog'lanish", url="https://t.me/adibnikjou")],
    ]

    back_button = Button.inline("⬅️ Asosiy menyu", b"back")

    setting_button = [
        [Button.inline("Yuklash usuli", b"setting/core")],
        [Button.inline("Sifat", b"setting/quality")],
        [Button.inline("X/Twitter skrinshot", b"setting/TweetCapture")],
        [Button.inline("Obuna", b"setting/subscription")],
        [back_button],
    ]

    back_button_to_setting = Button.inline("⬅️ Orqaga", b"setting/back")
    cancel_broadcast_button = [Button.inline("Bekor qilish", data=b"admin/cancel_broadcast")]

    admins_buttons = [
        [Button.inline("Xabar yuborish", b"admin/broadcast")],
        [Button.inline("Statistika", b"admin/stats")],
        [Button.inline("Yopish", b"cancel")],
    ]

    broadcast_options_buttons = [
        [Button.inline("Barcha foydalanuvchilarga", b"admin/broadcast/all")],
        [Button.inline("Faqat obunachilarga", b"admin/broadcast/subs")],
        [Button.inline("Faqat tanlangan IDlarga", b"admin/broadcast/specified")],
        [Button.inline("Bekor qilish", b"cancel")],
    ]

    continue_button = [Button.inline("Tekshirish", data=b"membership/continue")]
    cancel_subscription_button_quite = [Button.inline("Obunani bekor qilish", b"setting/subscription/cancel/quite")]
    cancel_button = [Button.inline("Bekor qilish", b"cancel")]

    @staticmethod
    def get_tweet_capture_setting_buttons(mode):
        return [
            [Button.inline(("🔹 " if mode == "0" else "") + "Yorug'", data=b"setting/TweetCapture/mode/0")],
            [Button.inline(("🔹 " if mode == "1" else "") + "Qorong'i", data=b"setting/TweetCapture/mode/1")],
            [Button.inline(("🔹 " if mode == "2" else "") + "Qora", data=b"setting/TweetCapture/mode/2")],
            [Buttons.back_button, Buttons.back_button_to_setting],
        ]

    @staticmethod
    def get_subscription_setting_buttons(subscription):
        if subscription:
            return [[Button.inline("Obunani bekor qilish", data=b"setting/subscription/cancel")], [Buttons.back_button, Buttons.back_button_to_setting]]
        return [[Button.inline("Obuna bo'lish", data=b"setting/subscription/add")], [Buttons.back_button, Buttons.back_button_to_setting]]

    @staticmethod
    def get_core_setting_buttons(core):
        core = core or "Auto"
        return [
            [Button.inline(("🔸 " if core == "Auto" else "") + "Avto", data=b"setting/core/auto")],
            [Button.inline(("🔸 " if core == "YoutubeDL" else "") + "YoutubeDL", b"setting/core/youtubedl")],
            [Button.inline(("🔸 " if core == "SpotDL" else "") + "SpotDL", b"setting/core/spotdl")],
            [Buttons.back_button, Buttons.back_button_to_setting],
        ]

    @staticmethod
    def get_quality_setting_buttons(music_quality):
        music_quality = music_quality or {"format": "mp3", "quality": "320"}
        quality = str(music_quality.get("quality", "320"))
        music_format = music_quality.get("format", "mp3")
        return [
            [Button.inline(("◽️ " if music_format == "flac" else "") + "FLAC", b"setting/quality/flac")],
            [Button.inline(("◽️ " if music_format == "mp3" and quality == "320" else "") + "MP3 (320)", b"setting/quality/mp3/320")],
            [Button.inline(("◽️ " if music_format == "mp3" and quality == "128" else "") + "MP3 (128)", b"setting/quality/mp3/128")],
            [Buttons.back_button, Buttons.back_button_to_setting],
        ]

    @staticmethod
    def get_search_result_buttons(sanitized_query, search_result, page=1) -> list:
        start = (page - 1) * 10
        end = start + 10
        visible = search_result[start:end]
        button_list = [
            [Button.inline(f"🎧 {details['track_name']} — {details['artist_name']} ({details['release_year']})", data=f"spotify/info/{details['track_id']}")]
            for details in visible
        ]
        navigation = []
        if page > 1:
            navigation.append(Button.inline("⬅️ Oldingi", f"prev_page/s/{sanitized_query}/page/{page - 1}"))
        if end < len(search_result):
            navigation.append(Button.inline("Keyingi ➡️", f"next_page/s/{sanitized_query}/page/{page + 1}"))
        if navigation:
            button_list.append(navigation)
        button_list.append([Button.inline("Bekor qilish", b"cancel")])
        return button_list

    @staticmethod
    def get_playlist_search_buttons(playlist_id, search_result, page=1) -> list:
        start = (page - 1) * 10
        end = start + 10
        visible = search_result[start:end]
        button_list = [
            [Button.inline(f"🎧 {details['track_name']} — {details['artist_name']} ({details['release_year']})", data=f"spotify/info/{details['track_id']}")]
            for details in visible
        ]
        navigation = []
        if page > 1:
            navigation.append(Button.inline("⬅️ Oldingi", f"prev_page/p/{playlist_id}/page/{page - 1}"))
        if end < len(search_result):
            navigation.append(Button.inline("Keyingi ➡️", f"next_page/p/{playlist_id}/page/{page + 1}"))
        if navigation:
            button_list.append(navigation)
        button_list.append([Button.inline("Bekor qilish", b"cancel")])
        return button_list
