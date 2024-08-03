from datetime import datetime
from pyrainbird import async_client


class RainbirdData:
    def __init__(
        self,
        date: str,
        time: str,
        zones_running: list[bool],
        rain_sensor: bool,
    ):
        self.date = date
        self.time = time
        self.zones = zones_running
        self.rain_sensor = rain_sensor

    @property
    def timestampString(self) -> str:
        return f"{self.date} {self.time}"

    @property
    def unixTimestamp(self) -> int:
        return int(self.datetime.timestamp())

    @property
    def datetime(self) -> datetime:
        return datetime.fromisoformat(self.timestampString)


async def get_rainbird_data(
    controller: async_client.AsyncRainbirdController,
) -> RainbirdData:
    date = await controller.get_current_date()
    time = await controller.get_current_time()

    zones = await controller.get_available_stations()
    states = await controller.get_zone_states()
    zones_running = [states.active(zone) for zone in zones.active_set]

    rain_sensor_state = await controller.get_rain_sensor_state()

    data = RainbirdData(
        date=str(date),
        time=str(time),
        zones_running=zones_running,
        rain_sensor=rain_sensor_state,
    )

    return data
