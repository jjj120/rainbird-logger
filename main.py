#!/usr/bin/env python


import logging, asyncio, aiohttp, os, datetime


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from dotenv import load_dotenv
import os
from rainbird_data import get_rainbird_data, RainbirdData
from pyrainbird import async_client
from database_functions import (
    create_sqlite_database,
    add_data,
    get_data_from_day,
    get_data_from_month,
)
from render_history_data import (
    render_history_data_day,
    render_history_data_month,
    int_to_month,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.DEBUG)

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


def check_int(s):
    if s[0] in ("-", "+"):
        return s[1:].isdigit()
    return s.isdigit()


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

/history
    day <opt:offset> - Show a graph of the days irrigation history
    yesterday - Show a graph of yesterdays irrigation history
    month <opt:offset> - Show a graph of the months irrigation history

You also get a notification if the rain sensor is deactivates irrigation at the specified time.
    """
    logger.debug("Help command issued")
    await update.message.reply_text(HELP_STRING)


async def irrigation_current_string() -> str:
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

        return message


async def check_irrigation_current(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Check if irrigation is running."""
    logger.debug("Checking current irrigation status")
    message = await irrigation_current_string()
    await update.message.reply_text(message)


async def irrigation_today_string() -> str:
    data_parsed = get_data_from_day(DATABASE_PATH)
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

    return message


async def check_irrigation_today(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Check if irrigation was running today."""
    logger.debug("Checking irrigation status for today")
    message = await irrigation_today_string()
    await update.message.reply_text(message)


async def rain_sensor_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if irrigation is running."""
    logger.debug("Checking current irrigation status")
    async with aiohttp.ClientSession() as session:
        controller: async_client.AsyncRainbirdController = (
            async_client.CreateController(session, RAINBIRD_IP, RAINBIRD_PASSWORD)
        )
        rainbird_data = await get_rainbird_data(controller)

        if telegram_available == True and rainbird_data.rain_sensor == True:
            await context.bot.send_message(
                context.job.chat_id, "Regensensor deaktiviert Bewässerung"
            )


async def save_data_to_db(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("Saving data to database")
    async with aiohttp.ClientSession() as session:
        controller: async_client.AsyncRainbirdController = (
            async_client.CreateController(session, RAINBIRD_IP, RAINBIRD_PASSWORD)
        )

        new_data = await get_rainbird_data(controller)
        add_data(DATABASE_PATH, new_data)


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an image."""
    logger.debug("Sending test image")
    await update.message.reply_photo(photo="https://telegram.org/img/t_logo.png")


async def send_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an image of the days history."""
    command = context.args[0]
    logger.debug("Sending history image with command: " + command)

    if command == "day":
        day_offset = context.args[1] if len(context.args) > 1 else "0"
        if not check_int(day_offset):
            await update.message.reply_text("Invalid day offset: " + day_offset)
            return

        day_offset = int(day_offset)

        render_history_data_day(
            get_data_from_day(DATABASE_PATH, day_offset),
            "tmp/img.png",
            day_offset,
        )
    elif command == "yesterday":
        render_history_data_day(
            get_data_from_day(DATABASE_PATH, day_offset=-1),
            "tmp/img.png",
            -1,
        )
    elif command == "month":
        month_offset = context.args[1] if len(context.args) > 1 else "0"
        if not check_int(month_offset):
            await update.message.reply_text("Invalid month offset: " + month_offset)
            return

        month_offset = int(month_offset)

        render_history_data_month(
            get_data_from_month(DATABASE_PATH, month_offset),
            "tmp/img.png",
            month_offset,
        )
    else:
        await update.message.reply_text(
            "Invalid command, use /history day <opt:offset> | yesterday | month <opt:offset>"
        )
        return
    await update.message.reply_photo(photo="tmp/img.png")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("Aktuell", callback_data="current"),
            InlineKeyboardButton("Heute", callback_data="today"),
        ],
        [InlineKeyboardButton("Vergangen", callback_data="history")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Hi! Wähle eine Option:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    await query.answer()
    back_button_keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("back", callback_data="back")]]
    )

    if query.data == "history":
        this_month = int_to_month(datetime.datetime.now().month)
        last_month = int_to_month((datetime.datetime.now().month - 1) % 12)
        last_last_month = int_to_month((datetime.datetime.now().month - 2) % 12)

        keyboard = [
            [InlineKeyboardButton("Heute", callback_data="hist_today")],
            [InlineKeyboardButton("Gestern", callback_data="hist_yesterday")],
            [InlineKeyboardButton(this_month, callback_data="hist_month_off_0")],
            [InlineKeyboardButton(last_month, callback_data="hist_month_off_1")],
            [InlineKeyboardButton(last_last_month, callback_data="hist_month_off_2")],
            [
                InlineKeyboardButton("---", callback_data="back"),
                InlineKeyboardButton("back", callback_data="back"),
                InlineKeyboardButton("---", callback_data="back"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Wähle eine Option:", reply_markup=reply_markup
        )
        return

    elif query.data == "current":
        message = await irrigation_current_string()
        await query.edit_message_text(text=message, reply_markup=back_button_keyboard)

    elif query.data == "today":
        message = await irrigation_today_string()
        await query.edit_message_text(text=message, reply_markup=back_button_keyboard)

    elif query.data == "back":
        keyboard = [
            [
                InlineKeyboardButton("Aktuell", callback_data="current"),
                InlineKeyboardButton("Heute", callback_data="today"),
            ],
            [InlineKeyboardButton("Vergangen", callback_data="history")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Hi! Wähle eine Option:", reply_markup=reply_markup
        )
        return

    elif query.data == "hist_today":
        render_history_data_day(
            get_data_from_day(DATABASE_PATH),
            "tmp/img.png",
        )
        await query.edit_message_text("Heute", reply_markup=back_button_keyboard)
        # await query.edit_message_media("tmp/img.png")
        await context.bot.send_photo(photo="tmp/img.png", chat_id=query.message.chat_id)

    elif query.data == "hist_yesterday":
        render_history_data_day(
            get_data_from_day(DATABASE_PATH, day_offset=-1),
            "tmp/img.png",
            -1,
        )
        await query.edit_message_text("Gestern", reply_markup=back_button_keyboard)
        await context.bot.send_photo(photo="tmp/img.png", chat_id=query.message.chat_id)

    elif query.data == "hist_month_off_0":
        render_history_data_month(
            get_data_from_month(DATABASE_PATH),
            "tmp/img.png",
        )
        await query.edit_message_text("Dieser Monat", reply_markup=back_button_keyboard)
        await context.bot.send_photo(photo="tmp/img.png", chat_id=query.message.chat_id)

    elif query.data == "hist_month_off_1":
        render_history_data_month(
            get_data_from_month(DATABASE_PATH, -1), "tmp/img.png", -1
        )
        await query.edit_message_text(
            "Letzter Monat", reply_markup=back_button_keyboard
        )
        await context.bot.send_photo(photo="tmp/img.png", chat_id=query.message.chat_id)

    elif query.data == "hist_month_off_2":
        render_history_data_month(
            get_data_from_month(DATABASE_PATH, -2), "tmp/img.png", -2
        )
        await query.edit_message_text(
            "Vorletzter Monat", reply_markup=back_button_keyboard
        )
        await context.bot.send_photo(photo="tmp/img.png", chat_id=query.message.chat_id)

    elif query.data == "nothing":
        pass
    else:
        query.edit_message_text("Invalid option")

    # await query.edit_message_text(text=f"Selected option: {query.data}")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # add different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("current", check_irrigation_current))
    application.add_handler(CommandHandler("today", check_irrigation_today))
    application.add_handler(CommandHandler("history", send_history))

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

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, do_nothing))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
