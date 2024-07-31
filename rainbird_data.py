from datetime import datetime


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
