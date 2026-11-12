"""Only this module executes analytical SQL. Identifiers come from code, never user SQL."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .schemas import AnalysisArgs

METRICS = {
    "national_demand_mw",
    "transmission_demand_mw",
    "embedded_wind_generation",
    "embedded_solar_generation",
}
PERIOD_NOTE = (
    "Settlement periods are date-dependent indices, not fixed UTC or local clock labels. "
    "2024-03-31 has 46 periods; 2024-10-27 has 50. Periods 49–50 have one observation each "
    "in the complete year. Means weight observed half-hours equally; MW is power, not MWh."
)


@contextmanager
def connect_readonly(path: Path):
    # as_uri quotes ?, # and spaces, preventing URI option injection through a configured path.
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        yield connection
    finally:
        connection.close()


class Database:
    def __init__(self, path: Path):
        self.path = path

    def analyse(self, args: AnalysisArgs) -> dict:
        metric = args.metric
        if metric not in METRICS:
            raise ValueError("unsupported metric")
        where = "settlement_date >= ? AND settlement_date < ?"
        params: list = ["2024-01-01", "2025-01-01"]
        if args.month is not None:
            where += " AND substr(settlement_date, 6, 2) = ?"
            params.append(f"{args.month:02d}")
        base = f"FROM energy_records WHERE {where}"
        if args.analysis == "monthly":
            sql = (
                f"SELECT substr(settlement_date,1,7) AS month, COUNT(*) AS observations, "
                f"AVG({metric}) AS mean_mw, MAX({metric}) AS peak_mw {base} "
                "GROUP BY month ORDER BY mean_mw DESC, month"
            )
        elif args.analysis == "period_profile":
            sql = (
                f"SELECT settlement_period, COUNT(*) AS observations, AVG({metric}) AS mean_mw "
                f"{base} GROUP BY settlement_period ORDER BY settlement_period"
            )
        elif args.analysis == "peak":
            # All tied peak records are returned (at most the annual row count).
            sql = (
                f"SELECT settlement_date, settlement_period, {metric} AS value_mw {base} "
                f"AND {metric} = (SELECT MAX({metric}) {base}) "
                "ORDER BY settlement_date, settlement_period"
            )
            params = params * 2
        else:
            sql = (
                f"SELECT COUNT(*) AS observations, AVG({metric}) AS mean_mw, "
                f"MIN({metric}) AS min_mw, MAX({metric}) AS max_mw {base}"
            )
        with connect_readonly(self.path) as conn:
            rows = [dict(row) for row in conn.execute(sql, params)]
            provenance = [
                row[0]
                for row in conn.execute(
                    "SELECT DISTINCT source_sha256 FROM energy_records "
                    "WHERE settlement_date >= '2024-01-01' AND settlement_date < '2025-01-01'"
                )
            ]
            coverage = dict(
                conn.execute(
                    "SELECT COUNT(*) AS observations, COUNT(DISTINCT settlement_date) AS days "
                    "FROM energy_records WHERE settlement_date >= '2024-01-01' "
                    "AND settlement_date < '2025-01-01'"
                ).fetchone()
            )
        return {
            "metric": metric,
            "unit": "MW",
            "analysis": args.analysis,
            "month_filter": args.month,
            "rows": rows,
            "source_sha256": provenance,
            "annual_coverage": coverage,
            "note": PERIOD_NOTE,
            "sql": sql,
            "parameters": params,
        }
