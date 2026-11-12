import sqlite3

import pytest

from energy_copilot.database import Database


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    with sqlite3.connect(path) as c:
        c.execute(
            "CREATE TABLE energy_records (settlement_date TEXT, settlement_period INTEGER, national_demand_mw INTEGER, transmission_demand_mw INTEGER, embedded_wind_generation INTEGER, embedded_solar_generation INTEGER, source_sha256 TEXT, PRIMARY KEY(settlement_date,settlement_period))"
        )
        c.executemany(
            "INSERT INTO energy_records VALUES (?,?,?,?,?,?,?)",
            [
                ("2024-01-01", 1, 100, 120, 20, 0, "fixture"),
                ("2024-01-01", 2, 200, 230, 30, 0, "fixture"),
                ("2024-02-01", 1, 300, 330, 40, 10, "fixture"),
                ("2024-03-31", 46, 300, 330, 40, 10, "fixture"),
                ("2024-10-27", 50, 150, 170, 15, 0, "fixture"),
                ("2023-01-01", 1, 9999, 9999, 0, 0, "fixture"),
            ],
        )
    return Database(path)
