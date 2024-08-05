import asyncio, aiohttp, os
from dotenv import load_dotenv
from pyrainbird import async_client
from rainbird_data import RainbirdData, get_rainbird_data

from database_functions import create_sqlite_database, add_data
from telegram_notification import send_notification

load_dotenv()

RAINBIRD_PASSWORD = os.getenv("RAINBIRD_PASSWORD")
RAINBIRD_IP = os.getenv("RAINBIRD_IP_ADDRESS")
DATABASE_PATH = os.getenv("DATABASE_PATH")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_NOTIFICATION_TEXT = os.getenv("TELEGRAM_NOTIFICATION_TEXT")
TELEGRAM_NOTIFICATION_TIME_HOUR = os.getenv("TELEGRAM_NOTIFICATION_TIME_HOUR")
TELEGRAM_NOTIFICATION_TIME_MINUTE = os.getenv("TELEGRAM_NOTIFICATION_TIME_MINUTE")

telegram_available = not (
    TELEGRAM_BOT_TOKEN is None
    or TELEGRAM_CHAT_ID is None
    or TELEGRAM_NOTIFICATION_TEXT is None
    or TELEGRAM_NOTIFICATION_TIME_HOUR is None
    or TELEGRAM_NOTIFICATION_TIME_MINUTE is None
)


# print(
#     "Logging in at",
#     RAINBIRD_IP,
#     "with password of length",
#     str(len(RAINBIRD_PASSWORD)),
#     "\n",
# )


if not os.path.exists(DATABASE_PATH):
    create_sqlite_database(DATABASE_PATH)


async def save_data() -> None:
    async with aiohttp.ClientSession() as session:
        controller: async_client.AsyncRainbirdController = (
            async_client.CreateController(session, RAINBIRD_IP, RAINBIRD_PASSWORD)
        )

        new_data = await get_rainbird_data(controller)
        add_data(DATABASE_PATH, new_data)


async def main() -> None:
    await save_data()


if __name__ == "__main__":
    asyncio.run(main())


"""
    await controller.get_model_and_version() -> pyrainbird.data.ModelAndVersion:
    await controller.get_available_stations() -> pyrainbird.data.AvailableStations:
    await controller.get_serial_number() -> str:
    await controller.get_current_time() -> datetime.time:
    await controller.set_current_time(value: datetime.time) -> None:
    await controller.get_current_date() -> datetime.date:
    await controller.set_current_date(value: datetime.date) -> None:
    await controller.get_wifi_params() -> pyrainbird.data.WifiParams:
    await controller.get_settings() -> pyrainbird.data.Settings:
    await controller.get_weather_adjustment_mask() -> pyrainbird.data.WeatherAdjustmentMask:
    await controller.get_zip_code() -> pyrainbird.data.ZipCode:
    await controller.get_program_info() -> pyrainbird.data.ProgramInfo:
    await controller.get_network_status() -> pyrainbird.data.NetworkStatus:
    await controller.get_server_mode() -> pyrainbird.data.ServerMode:
    await controller.water_budget(budget) -> pyrainbird.data.WaterBudget:
    await controller.get_rain_sensor_state() -> bool:
    await controller.get_zone_states() -> pyrainbird.data.States:
    await controller.get_zone_state(zone: int) -> bool:
    await controller.set_program(program: int) -> None:
    await controller.test_zone(zone: int) -> None:
    await controller.irrigate_zone(zone: int, minutes: int) -> None:
    await controller.stop_irrigation() -> None:
    await controller.get_rain_delay() -> int:
    await controller.set_rain_delay(days: int) -> None:
    await controller.advance_zone(param: int) -> None:
    await controller.get_current_irrigation() -> bool:
    await controller.get_schedule_and_settings(stick_id: str) -> pyrainbird.data.ScheduleAndSettings:
    await controller.get_weather_and_status(stick_id: str, country: str, zip_code: str) -> pyrainbird.data.WeatherAndStatus:
    await controller.get_combined_controller_state() -> pyrainbird.data.ControllerState:
    await controller.get_controller_firmware_version() -> pyrainbird.data.ControllerFirmwareVersion:
    await controller.get_schedule() -> pyrainbird.data.Schedule:
    await controller.get_schedule_command(command_code: str) -> dict[str, typing.Any]:
    await controller.test_command_support(command_id: int) -> bool:
    await controller.test_rpc_support(rpc: str) -> dict[str, typing.Any]:
"""
