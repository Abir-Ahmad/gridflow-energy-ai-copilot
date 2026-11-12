import sqlite3

import pytest
from pydantic import ValidationError

from energy_copilot.database import Database, connect_readonly
from energy_copilot.schemas import AnalysisArgs


def args(analysis="monthly", month=None, metric="national_demand_mw"):
    return AnalysisArgs(metric=metric, analysis=analysis, month=month)


def test_monthly_rank_and_year_filter(db):
    result = db.analyse(args())
    assert result["rows"][0] == {"month": "2024-02", "observations": 1, "mean_mw": 300.0, "peak_mw": 300}
    assert result["rows"][-1]["mean_mw"] == 150
    assert result["annual_coverage"]["observations"] == 5


def test_peak_ties(db):
    rows = db.analyse(args("peak"))["rows"]
    assert len(rows) == 2
    assert rows[1]["settlement_period"] == 46
    assert all(x["value_mw"] == 300 for x in rows)


def test_parameter_filter(db):
    result = db.analyse(args("peak", 1))
    assert result["rows"][0]["value_mw"] == 200
    assert result["parameters"] == ["2024-01-01", "2025-01-01", "01"] * 2


def test_profile_keeps_dst_indices(db):
    rows = db.analyse(args("period_profile"))["rows"]
    assert [r["settlement_period"] for r in rows] == [1, 2, 46, 50]
    assert rows[-1]["observations"] == 1
    assert not any("utc" in key for row in rows for key in row)


def test_summary(db):
    row = db.analyse(args("summary"))["rows"][0]
    assert row == {"observations": 5, "mean_mw": 210.0, "min_mw": 100, "max_mw": 300}


@pytest.mark.parametrize(
    "metric", ["transmission_demand_mw", "embedded_wind_generation", "embedded_solar_generation"]
)
def test_other_metrics(db, metric):
    assert db.analyse(args("summary", metric=metric))["rows"][0]["observations"] == 5


@pytest.mark.parametrize(
    "changes",
    [
        {"metric": "national_demand_mw); DROP TABLE energy_records;--"},
        {"month": "1 OR 1=1"},
        {"month": 0},
        {"month": 13},
        {"month": True},
        {"analysis": "delete"},
        {"sql": "DROP TABLE energy_records"},
    ],
)
def test_reject_untrusted_arguments(changes):
    values = {"metric": "national_demand_mw", "analysis": "summary", "month": None, **changes}
    with pytest.raises(ValidationError):
        AnalysisArgs(**values)


def test_database_read_only(db):
    with connect_readonly(db.path) as c:
        for sql in [
            "DELETE FROM energy_records",
            "CREATE TABLE hacked (x INTEGER)",
            "UPDATE energy_records SET national_demand_mw=0",
        ]:
            with pytest.raises(sqlite3.OperationalError):
                c.execute(sql)


def test_missing_db_not_created(tmp_path):
    path = tmp_path / "missing.db"
    with pytest.raises(sqlite3.OperationalError):
        Database(path).analyse(args())
    assert not path.exists()


def test_empty_filter(db):
    assert db.analyse(args("monthly", 12))["rows"] == []
    assert db.analyse(args("summary", 12))["rows"][0]["mean_mw"] is None
