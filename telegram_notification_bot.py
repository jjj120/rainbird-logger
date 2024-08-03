#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging, asyncio, aiohttp, os


from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import os
from rainbird_data import get_rainbird_data
from pyrainbird import async_client

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAINBIRD_PASSWORD = os.getenv("RAINBIRD_PASSWORD")
RAINBIRD_IP = os.getenv("RAINBIRD_IP_ADDRESS")


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def check_irrigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if irrigation is running."""
    async with aiohttp.ClientSession() as session:
        controller: async_client.AsyncRainbirdController = (
            async_client.CreateController(session, RAINBIRD_IP, RAINBIRD_PASSWORD)
        )
        rainbird_data = await get_rainbird_data(controller)

        message = ""
        if rainbird_data.rain_sensor:
            message += "Regensensor deaktiviert Bewässerung\n"
        else:
            message += "Regensensor aktiviert Bewässerung\n"

        for index, zone in enumerate(rainbird_data.zones):
            if zone:
                message += f"Zone {index} läuft\n"
            else:
                message += f"Zone {index} läuft nicht\n"

        await update.message.reply_text(message)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping the bot."""
    await update.message.reply_text("Pong")


async def do_nothing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Do nothing."""
    pass


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an image."""
    await update.message.reply_photo(photo="https://telegram.org/img/t_logo.png")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("check_irrigation", check_irrigation))
    application.add_handler(CommandHandler("check", check_irrigation))
    application.add_handler(CommandHandler("image", send_image))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, do_nothing))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
