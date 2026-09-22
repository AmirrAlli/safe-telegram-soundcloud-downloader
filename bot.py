# FA
# قبل از اجرای اسکریپت، برای امنیت بیشتر توکن ربات را در پاورشل تنظیم کنید:
# [Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN", "User")


# EN
# Before running the script, set your bot token in PowerShell for security:
# [Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN", "User")



import os
import requests

from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


def get_info(link):

    response = requests.get(link)

    soup = BeautifulSoup(response.text, "html.parser")

    song = soup.find("meta", property="twitter:title")
    artist_meta = soup.find("meta", {"name": "description"})
    picture = soup.find("meta", property="twitter:image")

    description = artist_meta["content"]
    parts = description.split()

    if "by" in parts and "on" in parts:

        in1 = parts.index("by")
        in2 = parts.index("on")

        name = parts[in1 + 1:in2]

        return " ".join(name), song["content"], picture["content"], description

    else:
        return None, None, None, None


def download_soundcloud(link, song, name):

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # باز کردن سایت
    # open site
    
    response = session.get(
        "https://www.klickaud.org/en17/",
        headers=headers
    )

    if response.status_code != 200:
        return None

    # گرفتن CSRF
    # get CSRF

    csrf_response = session.get(
        "https://www.klickaud.org/csrf-token-endpoint.php",
        headers={
            **headers,
            "Accept": "application/json",
            "Referer": "https://www.klickaud.org/en17/"
        }
    )

    if csrf_response.status_code != 200:
        return None

    try:
        csrf_token = csrf_response.json()["csrf_token"]
    except Exception:
        return None

    # ارسال لینک به 'KlickAud'
    # send link to 'KlickAud'

    download_response = session.post(
        "https://www.klickaud.org/download.php",
        data={
            "value": link,
            "csrf_token": csrf_token
        },
        headers={
            **headers,
            "Referer": "https://www.klickaud.org/en17/"
        }
    )

    if download_response.status_code != 200:
        return None

    text = download_response.text

    # پیدا کردن لینک MP3
    # find mp3 link

    index = text.find("&name=")

    if index == -1:
        return None

    start = text.rfind('"', 0, index)

    audio_url = text[start + 1:index]

    # دانلود فایل
    # download file

    audio = session.get(
        audio_url,
        headers={
            **headers,
            "Referer": "https://www.klickaud.org/"
        }
    )

    if audio.status_code != 200:
        return None

    if "audio/mpeg" not in audio.headers.get("Content-Type", ""):
        return None

    # ذخیره فایل
    # save file

    filename = f"{song} - {name}.mp3"

    for char in '<>:"/\\|?*':
        filename = filename.replace(char, "")

    with open(filename, "wb") as file:
        file.write(audio.content)

    return filename


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello my friend :) ")
    


async def meesage(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if "soundcloud.com" in text and "/" in text:

        name, song, picture, description = get_info(text)

        if song is not None:

            await update.message.reply_text(
                f"Song :'{song}'\nArtist :'{name}'"
            )

            await update.message.reply_photo(picture)

            await update.message.reply_text("⏳ Downloading...")

            filename = download_soundcloud(text, song, name)

            if filename:

                with open(filename, "rb") as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=song,
                        performer=name,
                        filename=filename
                    )

                os.remove(filename)

            else:

                await update.message.reply_text(
                    "❌ Download failed."
                )

        else:

            await update.message.reply_text(
                "❌ Your SoundCloud link is wrong :( "
            )

    else:

        await update.message.reply_text(
            "❌ This isn't a SoundCloud link :( "
        )


token = os.getenv("TELEGRAM_BOT_TOKEN")

app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        meesage
    )
)

print("Bot is running...")

app.run_polling()
