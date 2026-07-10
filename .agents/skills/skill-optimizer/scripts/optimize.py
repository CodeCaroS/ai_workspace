from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _copy_skill(skill: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(skill, destination)


def _init_run(args: argparse.Namespace) -> int:
    skill = args.skill.resolve()
    run_dir = args.run_dir.resolve()

    if not skill.exists():
        raise SystemExit(f"missing skill file: {skill}")
    if not run_dir.exists():
        run_dir.mkdir(parents=True)

    for name in ["baseline", "rollouts", "evaluations", "reflections", "candidates"]:
        (run_dir / name).mkdir(exist_ok=True)

    _copy_skill(skill, run_dir / "baseline" / "initial_skill.md")
    _copy_skill(skill, run_dir / "baseline" / "current_skill.md")
    _copy_skill(skill, run_dir / "baseline" / "best_skill.md")

    manifest = {
        "run_id": args.run_id,
        "skill": str(skill),
        "train": str(args.train.resolve()) if args.train else None,
        "validation": str(args.validation.resolve()) if args.validation else None,
        "test": str(args.test.resolve()) if args.test else None,
        "target_model": args.target_model,
        "optimizer_model": args.optimizer_model,
        "started_at": _utc_now(),
    }
    _write_text(run_dir / "manifest.json", json.dumps(manifest, indent=2))
    _write_text(run_dir / "summary.md", f"# Skill Optimization Run\n\n- Run ID: {args.run_id}\n- Skill: {skill}\n")
    _write_text(run_dir / "rejected-edits.jsonl", "")
    return 0


def _status(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"missing run directory: {run_dir}")

    payload = {
        "run_dir": str(run_dir),
        "baseline_exists": (run_dir / "baseline" / "best_skill.md").exists(),
        "has_manifest": (run_dir / "manifest.json").exists(),
        "has_summary": (run_dir / "summary.md").exists(),
        "candidate_count": len(list((run_dir / "candidates").glob("*"))) if (run_dir / "candidates").exists() else 0,
    }
    print(json.dumps(payload, indent=2))
    return 0


def _self_test() -> None:
    assert _utc_now().endswith("Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize and inspect skill optimization runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a run skeleton")
    init_parser.add_argument("--skill", type=Path, required=True)
    init_parser.add_argument("--run-dir", type=Path, required=True)
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--train", type=Path)
    init_parser.add_argument("--validation", type=Path)
    init_parser.add_argument("--test", type=Path)
    init_parser.add_argument("--target-model", default=None)
    init_parser.add_argument("--optimizer-model", default=None)

    status_parser = subparsers.add_parser("status", help="inspect an existing run")
    status_parser.add_argument("--run-dir", type=Path, required=True)

    subparsers.add_parser("self-test", help="run built-in checks")

    args = parser.parse_args(argv)

    if args.command == "self-test":
        _self_test()
        print("ok")
        return 0

    if args.command == "init":
        return _init_run(args)
    if args.command == "status":
        return _status(args)

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
