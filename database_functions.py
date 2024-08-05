import sqlite3, os
from rainbird_data import RainbirdData


def create_sqlite_database(filename):
    """create a database connection to the SQLite database"""
    conn = None
    try:
        filepath = os.path.join(os.getcwd(), filename)
        conn = sqlite3.connect(filepath, detect_types=sqlite3.PARSE_DECLTYPES)
        # Add entry to the database
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS rainbird_data (
                datetime timestamp PRIMARY KEY,
                zone_1 BOOLEAN,
                zone_2 BOOLEAN,
                zone_3 BOOLEAN,
                zone_4 BOOLEAN,
                zone_5 BOOLEAN,
                zone_6 BOOLEAN,
                zone_7 BOOLEAN,
                zone_8 BOOLEAN,
                rain_sensor BOOLEAN
            )
            """
        )
        conn.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def add_data(filename: str, data: RainbirdData) -> None:
    conn = None
    try:
        filepath = os.path.join(os.getcwd(), filename)
        conn = sqlite3.connect(filepath, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO rainbird_data (
                datetime,
                zone_1,
                zone_2,
                zone_3,
                zone_4,
                zone_5,
                zone_6,
                zone_7,
                zone_8,
                rain_sensor
            ) VALUES (
            """
            + ", ".join("?" * 10)
            + ")",
            (
                data.datetime,
                *data.zones,
                data.rain_sensor,
            ),
        )
        conn.commit()

    except sqlite3.Error as e:
        print("sqlite3:", e)
    finally:
        if conn:
            conn.close()


def line_to_rainbird_data(line: tuple) -> RainbirdData:
    return RainbirdData(
        date=line[0].date(),
        time=line[0].time(),
        zones_running=line[1:9],
        rain_sensor=line[9],
    )


def get_data_from_day(filename: str, day_offset: int = 0) -> list[RainbirdData]:
    conn = None
    data = []
    try:
        filepath = os.path.join(os.getcwd(), filename)
        conn = sqlite3.connect(filepath, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM rainbird_data WHERE date(datetime) = date('now', ?)
            """,
            (f"{day_offset} day",),
        )
        data = c.fetchall()
    except sqlite3.Error as e:
        print("sqlite3:", e)
    finally:
        if conn:
            conn.close()
    return [line_to_rainbird_data(line) for line in data]


def get_data_from_month(filename: str, month_offset: int = 0) -> list[RainbirdData]:
    conn = None
    data = []
    try:
        filepath = os.path.join(os.getcwd(), filename)
        conn = sqlite3.connect(filepath, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM rainbird_data WHERE strftime('%m', datetime) = strftime('%m', 'now', ?)
            """,
            (f"{month_offset} month",),
        )
        data = c.fetchall()
    except sqlite3.Error as e:
        print("sqlite3:", e)
    finally:
        if conn:
            conn.close()
    return [line_to_rainbird_data(line) for line in data]


if __name__ == "__main__":
    create_sqlite_database("rainbird.db")
