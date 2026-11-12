"""Component evaluation is NOT LLM question-answering accuracy. --live is explicit opt-in."""

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from energy_copilot.config import Settings
from energy_copilot.database import Database
from energy_copilot.llm import OpenAIRouter
from energy_copilot.retrieval import CORPUS, MODEL, Retriever
from energy_copilot.schemas import AnalysisArgs
from energy_copilot.service import Copilot


def close(a, b):
    return math.isclose(a, b, abs_tol=1e-8) if isinstance(b, (int, float)) else a == b


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live", action="store_true", help="Makes paid/credited API requests; requires existing access"
    )
    parser.add_argument("--csv", type=Path, help="Independent reconciliation against official CSV")
    parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation.json"))
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.live and not settings.api_key:
        parser.error("Set OPENAI_API_KEY privately first; no live calls were made")
    retriever = Retriever()
    service = Copilot(Database(settings.database), OpenAIRouter(settings.api_key, settings.model), retriever)
    results = []
    for case in json.loads(Path("evals/cases.json").read_text()):
        started = perf_counter()
        if case["kind"] == "refusal" and not args.live:
            results.append({"id": case["id"], "status": "not_run", "reason": "Requires real LLM routing"})
            continue
        try:
            if args.live:
                answer = service.answer(case["question"])
                matching = [e for e in answer.evidence if e.tool == case["tool"]]
                if case["kind"] == "numeric":
                    matching = [e for e in matching if e.arguments == case["arguments"]]
                    actual = matching[0].result["rows"][0][case["field"]] if matching else None
                    passed = actual is not None and close(actual, case["expected"])
                elif case["kind"] == "documentation":
                    actual = [s.id for s in answer.sources]
                    passed = any(x.startswith(case["expected_source_prefix"]) for x in actual)
                else:
                    actual = [e.tool for e in answer.evidence]
                    passed = actual == ["decline"]
            elif case["kind"] == "numeric":
                result = service.database.analyse(AnalysisArgs(**case["arguments"]))
                actual = result["rows"][0][case["field"]]
                passed = close(actual, case["expected"])
            else:
                actual = [s.id for s in retriever.search(case["question"])]
                passed = any(x.startswith(case["expected_source_prefix"]) for x in actual)
            results.append(
                {
                    "id": case["id"],
                    "status": "pass" if passed else "fail",
                    "actual": actual,
                    "duration_seconds": round(perf_counter() - started, 4),
                }
            )
        except Exception as exc:
            results.append({"id": case["id"], "status": "error", "error_type": type(exc).__name__})
    reconciliations = []
    if args.csv:
        rows = list(csv.DictReader(args.csv.open(encoding="utf-8-sig")))
        from datetime import datetime as dt

        dates = [dt.strptime(row["SETTLEMENT_DATE"], "%d-%b-%Y").date() for row in rows]
        for month in range(1, 13):
            values = [
                int(row["ND"]) for row, day in zip(rows, dates) if day.year == 2024 and day.month == month
            ]
            observed = service.database.analyse(
                AnalysisArgs(metric="national_demand_mw", analysis="summary", month=month)
            )["rows"][0]
            passed = (
                observed["observations"] == len(values)
                and close(observed["mean_mw"], sum(values) / len(values))
                and observed["max_mw"] == max(values)
            )
            reconciliations.append({"month": month, "status": "pass" if passed else "fail"})
        # All 50 period-index groups independently checked, including DST tails.
        profile = service.database.analyse(
            AnalysisArgs(metric="national_demand_mw", analysis="period_profile", month=None)
        )["rows"]
        for row in profile:
            values = [int(x["ND"]) for x in rows if int(x["SETTLEMENT_PERIOD"]) == row["settlement_period"]]
            passed = row["observations"] == len(values) and close(row["mean_mw"], sum(values) / len(values))
            reconciliations.append(
                {"period": row["settlement_period"], "status": "pass" if passed else "fail"}
            )
    report = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_llm" if args.live else "components_no_llm",
        "model": settings.model if args.live else None,
        "embedding_model": MODEL,
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(args.csv.read_bytes()).hexdigest() if args.csv else None,
        "results": results,
        "csv_reconciliations": reconciliations,
        "limitations": "Small authored regression set, not a held-out benchmark. Component mode executes expected tools directly and does not test routing, refusal or model grounding selection. Retrieval metric is expected-document hit@3, not answer accuracy.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(
        json.dumps(
            {
                "report": str(args.output),
                "passed": sum(x["status"] == "pass" for x in results),
                "not_run": sum(x["status"] == "not_run" for x in results),
                "reconciliations": len(reconciliations),
            }
        )
    )
    raise SystemExit(any(x["status"] in ("fail", "error") for x in results + reconciliations))


if __name__ == "__main__":
    main()
