from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from rainbird_data import RainbirdData
import os


def render_history_data_today(
    history_data_today: list[RainbirdData], filename: str = "tmp/img.png"
) -> None:
    """Render history data."""
    zones_number = 4
    colors = ["red", "green", "blue", "orange", "purple", "brown", "pink", "gray"]
    fmt = mdates.DateFormatter("%H:%M")

    # two line subplots, top one for zones, bottom one for rain sensor
    fig, axs = plt.subplots(2)
    # fig, axs = plt.subplots(zones_number + 1)

    times = [entry.datetime for entry in history_data_today]

    # zones subplot
    zones = [entry.zones for entry in history_data_today]
    zones = list(zip(*zones))

    for index, zone in enumerate(zones):
        if index >= zones_number:
            break
        axs[0].plot(times, zone, label=f"Zone {index}", color=colors[index])

    axs[0].legend(loc="upper right")

    for i, ax in enumerate(axs):
        axs[i].set_yticks([0, 1])
        axs[i].set_yticklabels(["Off", "On"])
        axs[i].xaxis.set_major_formatter(mdates.DateFormatter(""))  # hide x-axis labels
        axs[i].grid(True)

    # # rain sensor subplot
    # rain_sensor = [entry.rain_sensor for entry in history_data_today]
    # axs[zones_number].plot(times, rain_sensor, label="Rain Sensor")

    # # axs[zones_number].xaxis.set_major_locator(mdates.HourLocator(interval=1))
    # axs[zones_number].xaxis.set_major_formatter(fmt)

    rain_sensor = [entry.rain_sensor for entry in history_data_today]
    axs[1].plot(times, rain_sensor, label="Rain Sensor")

    # axs[1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
    axs[1].xaxis.set_major_formatter(fmt)
    axs[1].set_xlabel("Time")

    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    plt.savefig(filename)


def render_history_data_month(
    history_data_month: list[RainbirdData], filename: str = "tmp/img.png"
) -> None:
    """Render history data."""
    zones_number = 4
    colors = ["red", "green", "blue", "orange", "purple", "brown", "pink", "gray"]
    fmt = mdates.DateFormatter("%d")

    # two line subplots, top one for zones, bottom one for rain sensor
    fig, axs = plt.subplots(2)
    # fig, axs = plt.subplots(zones_number + 1)

    zones = {}
    rain_sensor = {}
    for entry in history_data_month:
        if entry.datetime.date() not in zones:
            zones[entry.datetime.date()] = [0] * 8
            rain_sensor[entry.datetime.date()] = False

        for index_zone, zone in enumerate(entry.zones):
            zones[entry.datetime.date()][index_zone] = (
                zone and not entry.rain_sensor
            ) or zones[entry.datetime.date()][index_zone]

            rain_sensor[entry.datetime.date()] = (
                rain_sensor[entry.datetime.date()] or entry.rain_sensor
            )

    times = list(zones.keys())
    zones = [zones[time] for time in times]
    zones = list(zip(*zones))
    print(times)
    print(zones)

    for index, zone in enumerate(zones):
        if index >= zones_number:
            break
        axs[0].scatter(times, zone, label=f"Zone {index}", color=colors[index])

    axs[0].legend(loc="upper right")

    for i, ax in enumerate(axs):
        axs[i].set_yticks([0, 1])
        axs[i].set_yticklabels(["Off", "On"])
        axs[i].xaxis.set_major_formatter(mdates.DateFormatter(""))  # hide x-axis labels
        axs[i].xaxis.set_major_locator(mdates.DayLocator(interval=1))
        axs[i].grid(True)

    # # rain sensor subplot
    # rain_sensor = [entry.rain_sensor for entry in history_data_today]
    # axs[zones_number].scatter(times, rain_sensor, label="Rain Sensor")

    # # axs[zones_number].xaxis.set_major_locator(mdates.HourLocator(interval=1))
    # axs[zones_number].xaxis.set_major_formatter(fmt)

    rain_sensor = [rain_sensor[time] for time in times]
    axs[1].scatter(times, rain_sensor, label="Rain Sensor")

    axs[1].xaxis.set_major_locator(mdates.DayLocator(interval=1))
    axs[1].xaxis.set_major_formatter(fmt)
    axs[1].set_xlabel("Time")

    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    plt.savefig(filename)


if __name__ == "__main__":
    import database_functions

    render_history_data_today(
        database_functions.get_data_from_today("rainbird.sqlite3"), "tmp/img_today.png"
    )

    render_history_data_month(
        database_functions.get_data_from_month("rainbird.sqlite3"), "tmp/img_month.png"
    )
