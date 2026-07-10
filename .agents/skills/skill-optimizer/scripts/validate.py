from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter_block(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], "\n".join(lines[index + 1 :])

    return [], text


def _frontmatter_has_key(lines: list[str], key: str) -> bool:
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(.+)?$")
    return any(pattern.match(line) for line in lines)


def validate_skill(path: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return ValidationResult(False, [f"missing file: {path}"], [])
    if path.suffix.lower() != ".md":
        warnings.append("skill file is not Markdown")

    text = _read_text(path)
    frontmatter, body = _frontmatter_block(text)
    if not frontmatter:
        errors.append("missing YAML frontmatter")
    else:
        if not _frontmatter_has_key(frontmatter, "name"):
            errors.append("frontmatter missing name")
        if not _frontmatter_has_key(frontmatter, "description"):
            errors.append("frontmatter missing description")

    if not re.search(r"^#\s+\S", body, re.M):
        warnings.append("body has no top-level heading")

    return ValidationResult(not errors, errors, warnings)


def validate_tasks(directory: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not directory.exists():
        return ValidationResult(False, [f"missing directory: {directory}"], [])
    if not directory.is_dir():
        return ValidationResult(False, [f"not a directory: {directory}"], [])

    task_files = sorted(
        p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".jsonl"}
    )
    if not task_files:
        warnings.append("no task files found")

    for file in task_files:
        if file.suffix.lower() == ".jsonl":
            for line_number, line in enumerate(_read_text(file).splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{file}:{line_number}: invalid JSONL: {exc.msg}")
                    continue
                _validate_task_record(record, errors, file, line_number)
        else:
            try:
                record = json.loads(_read_text(file))
            except json.JSONDecodeError as exc:
                errors.append(f"{file}: invalid JSON: {exc.msg}")
                continue
            _validate_task_record(record, errors, file, 1)

    return ValidationResult(not errors, errors, warnings)


def _validate_task_record(record: object, errors: list[str], file: Path, line_number: int) -> None:
    if not isinstance(record, dict):
        errors.append(f"{file}:{line_number}: task record must be an object")
        return

    required = ["id", "prompt"]
    for key in required:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{file}:{line_number}: missing or empty {key}")


def validate_run(directory: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not directory.exists():
        return ValidationResult(False, [f"missing directory: {directory}"], [])
    if not directory.is_dir():
        return ValidationResult(False, [f"not a directory: {directory}"], [])

    required = [
        "baseline",
        "rollouts",
        "evaluations",
        "reflections",
        "candidates",
    ]
    for name in required:
        if not (directory / name).exists():
            errors.append(f"missing run subdirectory: {name}")

    if not (directory / "summary.md").exists():
        warnings.append("summary.md missing")
    if not (directory / "rejected-edits.jsonl").exists():
        warnings.append("rejected-edits.jsonl missing")

    return ValidationResult(not errors, errors, warnings)


def _print_result(result: ValidationResult, as_json: bool) -> int:
    payload = {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")
        print("valid" if result.valid else "invalid")
    return 0 if result.valid else 1


def _self_test() -> None:
    skill = """---
name: sample
description: >
  Sample skill.
---

# Sample
"""
    fm, body = _frontmatter_block(skill)
    assert _frontmatter_has_key(fm, "name")
    assert _frontmatter_has_key(fm, "description")
    assert re.search(r"^#\s+\S", body, re.M)

    record = {"id": "task-1", "prompt": "Do thing"}
    errors: list[str] = []
    _validate_task_record(record, errors, Path("task.json"), 1)
    assert not errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill optimizer artifacts.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    skill_parser = subparsers.add_parser("skill", help="validate a SKILL.md file")
    skill_parser.add_argument("path", type=Path)

    tasks_parser = subparsers.add_parser("tasks", help="validate a task directory")
    tasks_parser.add_argument("path", type=Path)

    run_parser = subparsers.add_parser("run", help="validate a run directory")
    run_parser.add_argument("path", type=Path)

    subparsers.add_parser("self-test", help="run built-in checks")

    args = parser.parse_args(argv)

    if args.command == "self-test":
        _self_test()
        print("ok")
        return 0

    if args.command == "skill":
        return _print_result(validate_skill(args.path), args.json)
    if args.command == "tasks":
        return _print_result(validate_tasks(args.path), args.json)
    if args.command == "run":
        return _print_result(validate_run(args.path), args.json)

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
