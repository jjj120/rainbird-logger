#!/usr/bin/env python


import logging, asyncio, aiohttp, os, datetime


from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from dotenv import load_dotenv
import os, sqlite3
from rainbird_data import get_rainbird_data, RainbirdData
from pyrainbird import async_client
from database_functions import create_sqlite_database, add_data, get_data_from_today
from render_history_data import render_history_data_today, render_history_data_month

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAINBIRD_PASSWORD = os.getenv("RAINBIRD_PASSWORD")
RAINBIRD_IP = os.getenv("RAINBIRD_IP_ADDRESS")

DATABASE_PATH = os.getenv("DATABASE_PATH")
DATABASE_INTERVAL_MIN = os.getenv("DATABASE_INTERVAL_MIN")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS")

TELEGRAM_NOTIFICATION_TEXT = os.getenv("TELEGRAM_NOTIFICATION_TEXT")
TELEGRAM_NOTIFICATION_TIME_HOUR = os.getenv("TELEGRAM_NOTIFICATION_TIME_HOUR")
TELEGRAM_NOTIFICATION_TIME_MINUTE = os.getenv("TELEGRAM_NOTIFICATION_TIME_MINUTE")

telegram_available = not (
    TELEGRAM_BOT_TOKEN is None
    or TELEGRAM_CHAT_IDS is None
    or TELEGRAM_NOTIFICATION_TEXT is None
    or TELEGRAM_NOTIFICATION_TIME_HOUR is None
    or TELEGRAM_NOTIFICATION_TIME_MINUTE is None
)

if not os.path.exists(DATABASE_PATH):
    create_sqlite_database(DATABASE_PATH)


# Define command handlers. These usually take the two arguments update and context.
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping the bot."""
    await update.message.reply_text("Pong")


async def do_nothing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Do nothing."""
    pass


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    HELP_STRING = """
/start - Start the bot
/help - Show this help
/ping - Ping the bot (answers with pong)
/current - Check if irrigation is currently running and get rain sensor info
/today - Check if irrigation was running today

You also get a notification if the rain sensor is deactivates irrigation at the specified time.
    """
    await update.message.reply_text(HELP_STRING)


async def check_irrigation_current(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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


async def check_irrigation_today(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Check if irrigation was running today."""
    data_parsed = get_data_from_today(DATABASE_PATH)

    zones_today: list[bool] = [False] * 8
    for entry in data_parsed:
        for index, zone in enumerate(entry.zones):
            if zone and not entry.rain_sensor:
                zones_today[index] = True

    message = ""
    for index, zone in enumerate(zones_today):
        if zone:
            message += f"Zone {index} lief heute schon\n"
        else:
            message += f"Zone {index} lief heute nicht\n"

    await update.message.reply_text(message)


async def rain_sensor_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if irrigation is running."""
    async with aiohttp.ClientSession() as session:
        controller: async_client.AsyncRainbirdController = (
            async_client.CreateController(session, RAINBIRD_IP, RAINBIRD_PASSWORD)
        )
        rainbird_data = await get_rainbird_data(controller)

        if telegram_available == True and rainbird_data.rain_sensor == True:
            await context.bot.send_message(
                context.job.chat_id, "Regensensor deaktiviert Bewässerung"
            )


async def save_data_to_db() -> None:
    async with aiohttp.ClientSession() as session:
        controller: async_client.AsyncRainbirdController = (
            async_client.CreateController(session, RAINBIRD_IP, RAINBIRD_PASSWORD)
        )

        new_data = await get_rainbird_data(controller)
        add_data(DATABASE_PATH, new_data)


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an image."""
    await update.message.reply_photo(photo="https://telegram.org/img/t_logo.png")


async def send_history_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an image of the days history."""
    render_history_data_today(
        get_data_from_today("rainbird.sqlite3"), "tmp/img_today.png"
    )
    await update.message.reply_photo(photo="tmp/img_today.png")


async def send_history_month(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send an image of the months history."""
    render_history_data_month(
        get_data_from_today("rainbird.sqlite3"), "tmp/img_month.png"
    )
    await update.message.reply_photo(photo="tmp/img_month.png")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # add different commands - answer in Telegram
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("current", check_irrigation_current))
    application.add_handler(CommandHandler("today", check_irrigation_today))
    application.add_handler(CommandHandler("day", send_history_day))
    application.add_handler(CommandHandler("month", send_history_month))

    # Add daily timer for rain sensor notification
    for chat_id in TELEGRAM_CHAT_IDS.split(","):
        current_jobs = application.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()

        time = datetime.time(
            hour=int(TELEGRAM_NOTIFICATION_TIME_HOUR),
            minute=int(TELEGRAM_NOTIFICATION_TIME_MINUTE),
        )
        application.job_queue.run_daily(
            rain_sensor_notification, time, chat_id=chat_id, name=str(chat_id)
        )
        logger.info(f"Added weekly timer for chat {chat_id} at {time}")

    # Add data saving job
    application.job_queue.run_repeating(
        save_data_to_db, float(DATABASE_INTERVAL_MIN) * 60, name="data_save"
    )

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, do_nothing))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
