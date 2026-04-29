# MusicDownloader Telegram Bot

## O'zbekcha

MusicDownloader Telegram Bot — Spotify, YouTube, Instagram va X/Twitter havolalari bilan ishlaydigan, ovozli parcha orqali qo'shiq aniqlay oladigan Telegram bot. Loyiha Railway uchun tayyorlangan: muhit o'zgaruvchilari tashqariga chiqarilgan, `python main.py` orqali ishga tushadi, loglash qo'shilgan va foydalanuvchiga ko'rinadigan barcha asosiy matnlar o'zbek tiliga moslashtirilgan.

### Imkoniyatlar

- Spotify trek va playlist havolalarini qayta ishlash
- Matn bo'yicha qo'shiq qidirish
- YouTube format tanlash va fayl yuklash
- Instagram post, reel va story yuklash
- X/Twitter posti skrinshoti va media faylini olish
- Shazam orqali ovozli parchadan qo'shiqni aniqlash
- Sifat va yuklash yadrosini sozlash
- Admin uchun statistika va broadcast funksiyalari
- Railway uchun tayyor `Procfile`, `runtime.txt` va `.env.example`

### Tuzilma

```text
.
├── main.py
├── Procfile
├── runtime.txt
├── requirements.txt
├── .env.example
├── config.env
├── plugins/
│   ├── spotify.py
│   ├── youtube.py
│   ├── instagram.py
│   ├── x.py
│   └── shazam.py
├── run/
│   ├── bot.py
│   ├── buttons.py
│   ├── commands.py
│   ├── messages.py
│   ├── channel_checker.py
│   ├── version_checker.py
│   └── glob_variables.py
└── utils/
    ├── broadcast.py
    ├── database.py
    ├── helper.py
    ├── logger.py
    └── tweet_capture.py
```

### Muhit o'zgaruvchilari

Majburiy:

- `BOT_TOKEN`
- `API_ID`
- `API_HASH`

Tavsiya etiladi / funksiyaga bog'liq:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `GENIUS_ACCESS_TOKEN`

Ixtiyoriy:

- `CHANNEL_ID` — vergul bilan ajratilgan kanal username yoki ID lar
- `ADMIN_ID` — vergul bilan ajratilgan admin ID lar
- `LOG_LEVEL` — masalan: `INFO`, `DEBUG`
- `GOOGLE_CHROME_BIN`, `CHROMEDRIVER_PATH` — Railway yoki boshqa serverda Chromium yo'li kerak bo'lsa

### GitHub orqali o'rnatish

1. Repositoriyani klon qiling:
   ```bash
   git clone https://github.com/your-username/MusicDownloader-Telegram-Bot.git
   cd MusicDownloader-Telegram-Bot
   ```
2. Virtual muhit yarating:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
   Windows uchun:
   ```powershell
   .venv\Scripts\activate
   ```
3. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env.example` dan nusxa oling va o'z qiymatlaringizni kiriting:
   ```bash
   cp .env.example .env
   ```
5. Botni ishga tushiring:
   ```bash
   python main.py
   ```

### Railway deployment

1. Loyihani GitHub'ga yuklang.
2. Railway'da **New Project** → **Deploy from GitHub Repo** ni tanlang.
3. Repo ulanib bo'lgach, Variables bo'limida `.env.example` dagi qiymatlarni kiriting.
4. Railway avtomatik ravishda `runtime.txt` va `Procfile` asosida worker jarayonini ishga tushiradi.
5. Kerak bo'lsa FFmpeg va Chromium mavjudligini tekshiring.
6. Deploy tugagach, loglarda `Bot ishga tushdi` yozuvi chiqqanini tekshiring.

### Foydalanish misollari

- `/start` — botni boshlash
- `/help` — yo'riqnoma
- `/search Linkin Park Numb` — qidiruv
- Spotify yoki YouTube havolasini yuborish — to'g'ridan-to'g'ri qayta ishlash
- Ovozli xabar yuborish — qo'shiqni aniqlash

### Eslatmalar

- `config.env` va `.env.example` ichida haqiqiy tokenlar yo'q.
- `user_settings.db`, `repository/` va `__pycache__/` fayllarini GitHub'ga yuklamaslik tavsiya etiladi.
- Spotify matn va metadata funksiyalari uchun Spotify/Genius tokenlari kerak bo'lishi mumkin.

---

## English

MusicDownloader Telegram Bot is a Telegram bot for downloading media from Spotify, YouTube, Instagram, and X/Twitter, plus recognizing songs from short voice samples. This version is prepared for Railway deployment: secrets are externalized, logging is enabled, `python main.py` is the entry point, and the main user-facing texts are localized to Uzbek.

### Features

- Handles Spotify track and playlist links
- Searches songs by text query
- Lets users choose YouTube download formats
- Downloads Instagram posts, reels, and stories
- Captures X/Twitter post screenshots and media
- Recognizes songs from voice snippets via Shazam
- Supports quality and download-core settings
- Includes admin statistics and broadcast tools
- Ready for Railway with `Procfile`, `runtime.txt`, and `.env.example`

### Environment variables

Required:

- `BOT_TOKEN`
- `API_ID`
- `API_HASH`

Recommended / feature-dependent:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `GENIUS_ACCESS_TOKEN`

Optional:

- `CHANNEL_ID`
- `ADMIN_ID`
- `LOG_LEVEL`
- `GOOGLE_CHROME_BIN`
- `CHROMEDRIVER_PATH`

### Local installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill in your values.
5. Start the bot with `python main.py`.

### Railway deployment steps

1. Push the repository to GitHub.
2. Create a new Railway project from the GitHub repository.
3. Add the environment variables from `.env.example` in the Railway Variables section.
4. Railway will use `runtime.txt` and `Procfile` to start the worker.
5. Verify the logs after deployment.

### Usage examples

- `/start`
- `/help`
- `/search Adele Hello`
- Send a Spotify or YouTube link
- Send a voice message to identify a song

---

## O'zbekcha tarjima (English bo'limi)

MusicDownloader Telegram Bot — Spotify, YouTube, Instagram va X/Twitter'dan media yuklash, shuningdek qisqa ovozli parchadan qo'shiqni aniqlash uchun mo'ljallangan Telegram bot. Ushbu talqin Railway uchun tayyorlangan: maxfiy ma'lumotlar tashqariga chiqarilgan, loglash yoqilgan, kirish nuqtasi `python main.py`, foydalanuvchiga ko'rinadigan asosiy matnlar esa o'zbekchalashtirilgan.

### Asosiy imkoniyatlar

- Spotify trek va playlist havolalarini qo'llab-quvvatlaydi
- Matnli so'rov orqali qo'shiq qidiradi
- YouTube yuklash formatlarini tanlash imkonini beradi
- Instagram post, reel va story fayllarini yuklaydi
- X/Twitter postlari uchun skrinshot va media oladi
- Shazam orqali ovozli parchadan qo'shiqni aniqlaydi
- Sifat va yuklash yadrosi sozlamalarini qo'llaydi
- Admin uchun statistika va broadcast vositalari bor
- `Procfile`, `runtime.txt` va `.env.example` bilan Railway'ga tayyor

### Muhit o'zgaruvchilari

Majburiy qiymatlar:

- `BOT_TOKEN`
- `API_ID`
- `API_HASH`

Tavsiya etiladigan yoki funksiya bilan bog'liq qiymatlar:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `GENIUS_ACCESS_TOKEN`

Ixtiyoriy qiymatlar:

- `CHANNEL_ID`
- `ADMIN_ID`
- `LOG_LEVEL`
- `GOOGLE_CHROME_BIN`
- `CHROMEDRIVER_PATH`

### Lokal o'rnatish

1. Repositoriyani klon qiling.
2. Virtual muhit yarating va faollashtiring.
3. `pip install -r requirements.txt` orqali bog'liqliklarni o'rnating.
4. `.env.example` ni `.env` ga nusxalab, o'z qiymatlaringizni kiriting.
5. Botni `python main.py` orqali ishga tushiring.

### Railway deployment qadamlari

1. Reponi GitHub'ga joylang.
2. GitHub repodan yangi Railway loyiha yarating.
3. Railway Variables bo'limiga `.env.example` dagi qiymatlarni kiriting.
4. Railway `runtime.txt` va `Procfile` asosida worker jarayonini ishga tushiradi.
5. Deploydan keyin loglarni tekshiring.

### Foydalanish namunalari

- `/start`
- `/help`
- `/search Adele Hello`
- Spotify yoki YouTube havolasini yuborish
- Qo'shiqni aniqlash uchun ovozli xabar yuborish
