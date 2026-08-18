#!/usr/bin/env python3
"""Audit frozen Wan2.2 train/validation manifests and fail on leakage."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("video_path", "prompt", "source_dataset", "source_sequence_id", "split")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Expected object at {path}:{line_number}")
            rows.append(value)
    return rows


def resolve_video(value: str, base_path: Path | None) -> Path | None:
    if value.startswith(("http://", "https://")):
        return None
    path = Path(os.path.expanduser(os.path.expandvars(value)))
    if not path.is_absolute() and base_path is not None:
        path = base_path / path
    return path.resolve(strict=False)


def audit(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    train = read_jsonl(args.train)
    val = read_jsonl(args.val)
    failures: list[str] = []
    all_rows = train + val
    expected_split = {id(row): "train" for row in train}
    expected_split.update({id(row): "val" for row in val})

    missing_required: Counter[str] = Counter()
    bad_split = 0
    empty_caption = 0
    short_caption = 0
    template_caption = 0
    missing_file = 0
    duplicate_videos: list[str] = []
    seen_videos: set[str] = set()
    pattern = re.compile(r"\b(?:video[_ -]?id|file(?:name)?)\s*:", re.IGNORECASE)

    for row in all_rows:
        for field in REQUIRED_FIELDS:
            if field not in row or row[field] is None or not str(row[field]).strip():
                missing_required[field] += 1
        if row.get("split") != expected_split[id(row)]:
            bad_split += 1
        caption = re.sub(r"\s+", " ", str(row.get("prompt", ""))).strip()
        if not caption:
            empty_caption += 1
        elif len(caption) < args.min_caption_chars:
            short_caption += 1
        if pattern.search(caption):
            template_caption += 1
        video = str(row.get("video_path", ""))
        if video in seen_videos:
            duplicate_videos.append(video)
        seen_videos.add(video)
        if args.check_files and video:
            resolved = resolve_video(video, args.base_path)
            if resolved is not None and not resolved.is_file():
                missing_file += 1

    train_sequences = {str(row.get("source_sequence_id", "")) for row in train}
    val_sequences = {str(row.get("source_sequence_id", "")) for row in val}
    leakage = sorted((train_sequences & val_sequences) - {""})
    source_counts = Counter(str(row.get("source_dataset", "")) for row in all_rows)
    train_source_counts = Counter(str(row.get("source_dataset", "")) for row in train)
    total = len(all_rows)
    train_total = len(train)
    source_fractions = {
        source: round(count / total, 6) if total else 0.0
        for source, count in sorted(source_counts.items())
    }
    train_source_fractions = {
        source: round(count / train_total, 6) if train_total else 0.0
        for source, count in sorted(train_source_counts.items())
    }
    overrepresented = {
        source: fraction
        for source, fraction in train_source_fractions.items()
        if fraction > args.max_source_fraction + 1e-12
    }

    if not train:
        failures.append("training split is empty")
    if missing_required:
        failures.append(f"missing required fields: {dict(missing_required)}")
    if bad_split:
        failures.append(f"{bad_split} rows have the wrong split label")
    if empty_caption:
        failures.append(f"{empty_caption} rows have empty captions")
    if short_caption:
        failures.append(f"{short_caption} rows have captions shorter than {args.min_caption_chars}")
    if template_caption:
        failures.append(f"{template_caption} rows contain video/file IDs in captions")
    if duplicate_videos:
        failures.append(f"{len(duplicate_videos)} duplicate video paths")
    if leakage:
        failures.append(f"{len(leakage)} source sequences leak across train/val")
    if missing_file:
        failures.append(f"{missing_file} video files are missing")
    if overrepresented:
        failures.append(f"source fraction limit exceeded: {overrepresented}")

    report = {
        "schema_version": 1,
        "train_path": str(args.train.resolve()),
        "val_path": str(args.val.resolve()),
        "train_count": len(train),
        "val_count": len(val),
        "source_fractions": source_fractions,
        "train_source_fractions": train_source_fractions,
        "missing_required": dict(missing_required),
        "bad_split": bad_split,
        "empty_caption": empty_caption,
        "short_caption": short_caption,
        "template_caption": template_caption,
        "duplicate_video_count": len(duplicate_videos),
        "sequence_leakage_count": len(leakage),
        "sequence_leakage_examples": leakage[:20],
        "missing_file_count": missing_file,
        "failures": failures,
        "passed": not failures,
    }
    return report, failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--val", type=Path, required=True)
    parser.add_argument("--base-path", type=Path)
    parser.add_argument("--check-files", action="store_true")
    parser.add_argument("--min-caption-chars", type=int, default=24)
    parser.add_argument("--max-source-fraction", type=float, default=0.30)
    parser.add_argument("--report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report, failures = audit(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
