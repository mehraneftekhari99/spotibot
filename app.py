import re
import os
import telebot
from savify import Savify
from savify.types import Format, Quality
from savify.utils import PathHolder
from savify.logger import Logger
from dotenv import load_dotenv

load_dotenv()


logger = Logger(log_location=".", log_level=None)  # will write to ./logs/

# Get secrets values from environment variables (or .env file)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


savify = Savify(
    api_credentials=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    quality=Quality.BEST,
    download_format=Format.MP3,
    path_holder=PathHolder(data_path="./data", downloads_path="./downloads"),
    group="%artist%/%album%",
    skip_cover_art=False,
    logger=logger,
)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def _is_valid_spotify_link(link):
    # Check if the link starts with the Spotify track URL
    if not link.startswith("https://open.spotify.com/track/"):
        return False

    # Extract the part of the URL after "track/"
    track_id = link.split("https://open.spotify.com/track/")[1].split("?")[0]

    # Check if the track ID matches the Spotify format (22 alphanumeric characters)
    return bool(re.match("^[0-9a-zA-Z]{22}$", track_id))


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, "Hi. Send me a link to Spotify track.")


@bot.message_handler(func=lambda message: True)
def save_track(message):
    # check if message is a valid spotify link
    if not _is_valid_spotify_link(message.text):
        bot.reply_to(message, "Invalid Spotify link.")
        return

    # set downloading status
    bot.send_chat_action(message.chat.id, "record_voice")

    # download track
    try:
        t = savify._parse_query(message.text)
        file_loc = savify._download(t[0])["location"]
    except:
        bot.reply_to(message, "Error downloading track.")
        return

    bot.send_chat_action(message.chat.id, "upload_voice")

    # send track to user
    with open(file_loc, "rb") as f:
        bot.send_audio(message.chat.id, f, timeout=60)


if __name__ == "__main__":
    bot.infinity_polling()
