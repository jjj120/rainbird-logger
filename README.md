# Rainbird Logger

This is a simple logger for the Rainbird irrigation system. It logs the current state of the system to a sqlite database file.

## Installation

Clone the repository and install the required packages:

```bash
pip install -r requirements.txt
chmod u+x run.sh
```

### Configuration

Add a file named `.env` in the root directory with the following content:

```bash
RAINBIRD_IP="<IP_ADDRESS>"
RAINBIRD_PASSWORD="<PASSWORD>"
DATABASE_PATH="rainbird.sqlite3"
```

## Usage

```bash
./run.sh
```

Each time the script is run, it will log the current state of the system to the database.

The database schema is as follows:

```sql
CREATE TABLE IF NOT EXISTS rainbird_data (
    datetime timestamp PRIMARY KEY,
    zone1 BOOLEAN,
    zone2 BOOLEAN,
    zone3 BOOLEAN,
    zone4 BOOLEAN,
    zone5 BOOLEAN,
    zone6 BOOLEAN,
    zone7 BOOLEAN,
    zone8 BOOLEAN,
    rain_sensor BOOLEAN
);
```

It only stores the current irrigation state of each zone and the state of the rain sensor. The timestamp is the primary key.
