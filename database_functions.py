import sqlite3
from rainbird_data import RainbirdData


def create_sqlite_database(filename):
    """create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
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
        conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
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


if __name__ == "__main__":
    create_sqlite_database("rainbird.db")