from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


@dataclass
class ScoreSummary:
    count: int
    hard_score: float
    soft_score: float
    dimensions: dict[str, float]


def _load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    if path.is_dir():
        files = sorted(
            p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".jsonl"}
        )
        for file in files:
            records.extend(_load_records(file))
        return records

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return records
    if path.suffix.lower() == ".jsonl":
        for line in text.splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    loaded = json.loads(text)
    if isinstance(loaded, list):
        for item in loaded:
            if isinstance(item, dict):
                records.append(item)
    elif isinstance(loaded, dict):
        if "evaluations" in loaded and isinstance(loaded["evaluations"], list):
            for item in loaded["evaluations"]:
                if isinstance(item, dict):
                    records.append(item)
        else:
            records.append(loaded)
    return records


def _dimensions(record: dict) -> dict[str, float]:
    raw = record.get("dimensions", {})
    return raw if isinstance(raw, dict) else {}


def _summary(records: list[dict]) -> ScoreSummary:
    if not records:
        return ScoreSummary(0, 0.0, 0.0, {})

    hard_values = [float(record.get("hard_score", 0.0)) for record in records]
    soft_values = [float(record.get("soft_score", 0.0)) for record in records]
    dimension_names = sorted({name for record in records for name in _dimensions(record)})
    dimensions = {
        name: mean(
            float(_dimensions(record).get(name, 0.0))
            for record in records
        )
        for name in dimension_names
    }
    return ScoreSummary(len(records), mean(hard_values), mean(soft_values), dimensions)


def _composite(summary: ScoreSummary, hard_weight: float, soft_weight: float) -> float:
    total = hard_weight + soft_weight
    if total <= 0:
        raise ValueError("weights must be positive")
    hard_weight /= total
    soft_weight /= total
    return hard_weight * summary.hard_score + soft_weight * summary.soft_score


def _compare(
    baseline: ScoreSummary,
    candidate: ScoreSummary,
    hard_weight: float,
    soft_weight: float,
    minimum_delta: float,
    critical_dimensions: list[str],
    critical_tolerance: float,
) -> dict:
    baseline_score = _composite(baseline, hard_weight, soft_weight)
    candidate_score = _composite(candidate, hard_weight, soft_weight)
    delta = candidate_score - baseline_score

    regressions = {}
    for name in critical_dimensions:
        before = baseline.dimensions.get(name)
        after = candidate.dimensions.get(name)
        if before is None or after is None:
            continue
        diff = after - before
        if diff < -critical_tolerance:
            regressions[name] = diff

    verdict = "accept" if delta > minimum_delta and not regressions else "reject"
    return {
        "baseline": {
            "count": baseline.count,
            "hard_score": baseline.hard_score,
            "soft_score": baseline.soft_score,
            "dimensions": baseline.dimensions,
            "composite": baseline_score,
        },
        "candidate": {
            "count": candidate.count,
            "hard_score": candidate.hard_score,
            "soft_score": candidate.soft_score,
            "dimensions": candidate.dimensions,
            "composite": candidate_score,
        },
        "delta": delta,
        "minimum_delta": minimum_delta,
        "critical_regressions": regressions,
        "verdict": verdict,
    }


def _self_test() -> None:
    baseline = _summary([{"hard_score": 0.6, "soft_score": 0.5, "dimensions": {"correctness": 0.8}}])
    candidate = _summary([{"hard_score": 0.9, "soft_score": 0.7, "dimensions": {"correctness": 0.9}}])
    result = _compare(baseline, candidate, 0.7, 0.3, 0.01, ["correctness"], 0.0)
    assert result["verdict"] == "accept"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate skill optimization rollouts.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    aggregate_parser = subparsers.add_parser("aggregate", help="aggregate one evaluation set")
    aggregate_parser.add_argument("path", type=Path)

    compare_parser = subparsers.add_parser("compare", help="compare baseline and candidate scores")
    compare_parser.add_argument("baseline", type=Path)
    compare_parser.add_argument("candidate", type=Path)
    compare_parser.add_argument("--hard-weight", type=float, default=0.7)
    compare_parser.add_argument("--soft-weight", type=float, default=0.3)
    compare_parser.add_argument("--minimum-delta", type=float, default=0.01)
    compare_parser.add_argument(
        "--critical-dimension",
        action="append",
        default=[],
        dest="critical_dimensions",
        help="dimension that must not regress",
    )
    compare_parser.add_argument("--critical-tolerance", type=float, default=0.0)

    subparsers.add_parser("self-test", help="run built-in checks")

    args = parser.parse_args(argv)

    if args.command == "self-test":
        _self_test()
        print("ok")
        return 0

    if args.command == "aggregate":
        summary = _summary(_load_records(args.path))
        payload = {
            "count": summary.count,
            "hard_score": summary.hard_score,
            "soft_score": summary.soft_score,
            "dimensions": summary.dimensions,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(json.dumps(payload, indent=2))
        return 0

    if args.command == "compare":
        baseline = _summary(_load_records(args.baseline))
        candidate = _summary(_load_records(args.candidate))
        payload = _compare(
            baseline,
            candidate,
            args.hard_weight,
            args.soft_weight,
            args.minimum_delta,
            args.critical_dimensions,
            args.critical_tolerance,
        )
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(json.dumps(payload, indent=2))
        return 0 if payload["verdict"] == "accept" else 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
