from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from rainbird_data import RainbirdData
import os, datetime

ACTIVE_ZONES = 3
COLORS = [
    "red",
    "darkgreen",
    "dodgerblue",
    "orange",
    "purple",
    "brown",
    "pink",
    "gray",
]
COLOR_RAIN_SENSOR = "darkgrey"
ZONE_ALIAS = {
    2: "Glashaus",
}


def render_history_data_day(
    history_data_today: list[RainbirdData],
    filename: str = "tmp/img.png",
    day_offset: int = 0,
) -> None:
    """Render history data."""
    fmt = mdates.DateFormatter("%H:%M")

    # two line subplots, top one for zones, bottom one for rain sensor
    fig, axs = plt.subplots(2)

    fig.suptitle(
        _day_offset_to_string(day_offset)
        + " - "
        + str(history_data_today[0].datetime.date()),
        fontsize=20,
    )

    times = [entry.datetime for entry in history_data_today]

    # zones subplot
    zones = [entry.zones for entry in history_data_today]
    zones = list(zip(*zones))

    for index, zone in enumerate(zones):
        if index >= ACTIVE_ZONES:
            break
        if index + 1 in ZONE_ALIAS.keys():
            axs[0].plot(
                times,
                zone,
                label=f"Zone {index+1} - {ZONE_ALIAS[index+1]}",
                color=COLORS[index],
            )
        else:
            axs[0].plot(times, zone, label=f"Zone {index+1}", color=COLORS[index])

    axs[0].legend(loc="upper right")

    for i, ax in enumerate(axs):
        axs[i].set_yticks([0, 1])
        axs[i].set_yticklabels(["Off", "On"])
        axs[i].xaxis.set_major_formatter(mdates.DateFormatter(""))  # hide x-axis labels
        axs[i].grid(True)

    rain_sensor = [entry.rain_sensor for entry in history_data_today]
    axs[1].plot(times, rain_sensor, label="Rain Sensor", color=COLOR_RAIN_SENSOR)

    axs[1].xaxis.set_major_formatter(fmt)
    axs[1].set_xlabel("Time")

    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    plt.savefig(filename, dpi=300)


def render_history_data_month(
    history_data_month: list[RainbirdData],
    filename: str = "tmp/img.png",
    month_offset: int = 0,
) -> None:
    """Render history data."""
    fmt = mdates.DateFormatter("%d")

    fig, axs = plt.subplots(2)

    if len(history_data_month) < 1:
        print("No data available for this month.")
        return

    month = (history_data_month[0].datetime.month + month_offset) % 12
    year = (
        history_data_month[0].datetime.year
        + (history_data_month[0].datetime.month + month_offset) // 12
    )

    fig.suptitle(int_to_month(month) + " " + str(year), fontsize=20)

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

    for index, zone in enumerate(zones):
        if index >= ACTIVE_ZONES:
            break

        # shift time to avoid overlapping of dots
        times_shifted = [
            datetime.datetime(time.year, time.month, time.day, index, 0, 0)
            for time in times
        ]
        if index + 1 in ZONE_ALIAS.keys():
            axs[0].scatter(
                times_shifted,
                zone,
                label=f"Zone {index+1} - {ZONE_ALIAS[index+1]}",
                color=COLORS[index],
            )
        else:
            axs[0].scatter(
                times_shifted, zone, label=f"Zone {index+1}", color=COLORS[index]
            )

    axs[0].legend(loc="upper right")

    for i, ax in enumerate(axs):
        axs[i].set_yticks([0, 1])
        axs[i].set_yticklabels(["Off", "On"])
        axs[i].xaxis.set_major_formatter(mdates.DateFormatter(""))  # hide x-axis labels
        axs[i].xaxis.set_major_locator(mdates.DayLocator(interval=1))
        axs[i].grid(True)

    rain_sensor = [rain_sensor[time] for time in times]
    axs[1].scatter(times, rain_sensor, label="Rain Sensor", color=COLOR_RAIN_SENSOR)

    axs[1].xaxis.set_major_locator(mdates.DayLocator(interval=1))
    axs[1].xaxis.set_major_formatter(fmt)
    axs[1].set_xlabel("Time")

    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    plt.savefig(filename, dpi=300)


def int_to_month(month: int) -> str:
    """Convert month number to month name."""
    months = [
        "Jänner",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]
    return months[month - 1]


def _day_offset_to_string(day_offset: int) -> str:
    """Convert day offset to string."""
    if day_offset == 0:
        return "Heute"
    elif day_offset == -1:
        return "Gestern"
    elif day_offset == 1:
        return "Vorgestern"
    else:
        return f"Vor {abs(day_offset)} Tagen"


if __name__ == "__main__":
    import database_functions

    render_history_data_day(
        database_functions.get_data_from_day("rainbird.sqlite3"), "tmp/img_today.png"
    )

    render_history_data_day(
        database_functions.get_data_from_day("rainbird.sqlite3", -1),
        "tmp/img_yesterday.png",
        -1,
    )

    render_history_data_month(
        database_functions.get_data_from_month("rainbird.sqlite3"), "tmp/img_month.png"
    )
