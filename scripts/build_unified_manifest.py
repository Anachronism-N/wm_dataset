#!/usr/bin/env python3
"""Build reproducible, group-isolated Wan2.2 experiment manifests.

The old version of this script embedded one cluster path and silently accepted
empty or template captions. This implementation is driven by a JSON source
specification, freezes every input hash, and writes both rich JSONL manifests
and the two-column CSV consumed by DiffSynth-Studio.

Example:
    export WM_DATA_ROOT=/path/to/wm_dataset
    python scripts/build_unified_manifest.py \
        --config training_metadata/experiment_sources.example.json \
        --phase smoke --check-files
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DEFAULT_VIDEO_FIELDS = ("video_path", "video")
DEFAULT_CAPTION_FIELDS = ("prompt", "caption", "caption_i2v")
DEFAULT_SEQUENCE_FIELDS = (
    "source_sequence_id",
    "source_video_id",
    "original_video_id",
    "sample_id",
    "video_id",
)


class ManifestBuildError(RuntimeError):
    """Raised when an experiment manifest cannot be frozen safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_score(seed: int, *parts: object) -> str:
    value = "\x1f".join([str(seed), *(str(part) for part in parts)])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def expand_path(value: str, *, relative_to: Path) -> Path:
    expanded = os.path.expanduser(os.path.expandvars(str(value)))
    if "$" in expanded:
        raise ManifestBuildError(
            f"Unresolved environment variable in path: {value!r}. "
            "Set WM_DATA_ROOT (or the variable used by the config)."
        )
    path = Path(expanded)
    if not path.is_absolute():
        path = relative_to / path
    return path.resolve(strict=False)


def iter_manifest(path: Path) -> Iterator[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)
        return
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ManifestBuildError(f"JSON manifest must contain a list: {path}")
        for row in payload:
            if isinstance(row, dict):
                yield row
        return
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ManifestBuildError(
                        f"Invalid JSONL at {path}:{line_number}: {exc}"
                    ) from exc
                if not isinstance(row, dict):
                    raise ManifestBuildError(
                        f"Expected an object at {path}:{line_number}"
                    )
                yield row
        return
    raise ManifestBuildError(f"Unsupported manifest format: {path}")


def first_value(row: dict[str, Any], fields: Iterable[str]) -> Any:
    for field in fields:
        value = row.get(field)
        if value is not None and str(value).strip():
            return value
    return None


def normalize_caption(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def derive_sequence_id(video_path: str) -> str:
    stem = Path(video_path).stem
    return re.sub(r"[_-]\d{3,6}$", "", stem)


def resolve_video_path(
    raw_value: Any,
    *,
    source_base: Path,
    dataset_base: Path,
    emit_relative_paths: bool,
) -> tuple[str, Path | None]:
    raw = str(raw_value).strip()
    if raw.startswith(("http://", "https://")):
        return raw, None
    expanded = os.path.expanduser(os.path.expandvars(raw))
    if "$" in expanded:
        raise ManifestBuildError(f"Unresolved environment variable in video path: {raw}")
    candidate = Path(expanded)
    resolved = candidate if candidate.is_absolute() else source_base / candidate
    resolved = resolved.resolve(strict=False)
    if not emit_relative_paths:
        return str(resolved), resolved
    try:
        return resolved.relative_to(dataset_base).as_posix(), resolved
    except ValueError:
        return str(resolved), resolved


def caption_rejection_reason(
    caption: str,
    *,
    min_chars: int,
    max_chars: int,
    reject_patterns: list[re.Pattern[str]],
) -> str | None:
    if not caption:
        return "empty_caption"
    if len(caption) < min_chars:
        return "caption_too_short"
    if len(caption) > max_chars:
        return "caption_too_long"
    for pattern in reject_patterns:
        if pattern.search(caption):
            return f"caption_pattern:{pattern.pattern}"
    return None


def load_source(
    source: dict[str, Any],
    *,
    phase: str,
    config_dir: Path,
    dataset_base: Path,
    seed: int,
    quality: dict[str, Any],
    check_files: bool,
    emit_relative_paths: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    name = str(source["name"])
    quota = int(source.get("quotas", {}).get(phase, 0))
    stats: dict[str, Any] = {
        "manifest": None,
        "input_sha256": None,
        "quota": quota,
        "read": 0,
        "selected": 0,
        "shortfall": 0,
        "rejected": Counter(),
    }
    if not source.get("enabled", True) or quota <= 0:
        stats["status"] = "disabled_for_phase"
        stats["rejected"] = {}
        return [], stats

    manifest = expand_path(str(source["manifest"]), relative_to=config_dir)
    stats["manifest"] = str(manifest)
    if not manifest.is_file():
        raise ManifestBuildError(f"Source {name!r} manifest does not exist: {manifest}")
    stats["input_sha256"] = sha256_file(manifest)

    source_base_value = source.get("base_path")
    source_base = (
        expand_path(str(source_base_value), relative_to=config_dir)
        if source_base_value
        else dataset_base
    )
    video_fields = source.get("video_fields", DEFAULT_VIDEO_FIELDS)
    caption_fields = source.get("caption_fields", DEFAULT_CAPTION_FIELDS)
    sequence_fields = source.get("sequence_fields", DEFAULT_SEQUENCE_FIELDS)
    min_chars = int(source.get("min_caption_chars", quality["min_chars"]))
    max_chars = int(source.get("max_caption_chars", quality["max_chars"]))
    patterns = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in [*quality.get("reject_patterns", []), *source.get("reject_patterns", [])]
    ]
    max_caption_repeats = int(
        source.get("max_exact_caption_repeats", quality["max_exact_caption_repeats"])
    )

    candidates: list[dict[str, Any]] = []
    seen_videos: set[str] = set()
    for row in iter_manifest(manifest):
        stats["read"] += 1
        video_value = first_value(row, video_fields)
        if video_value is None:
            stats["rejected"]["missing_video_field"] += 1
            continue
        caption = normalize_caption(first_value(row, caption_fields))
        reason = caption_rejection_reason(
            caption,
            min_chars=min_chars,
            max_chars=max_chars,
            reject_patterns=patterns,
        )
        if reason:
            stats["rejected"][reason] += 1
            continue
        video, resolved = resolve_video_path(
            video_value,
            source_base=source_base,
            dataset_base=dataset_base,
            emit_relative_paths=emit_relative_paths,
        )
        if video in seen_videos:
            stats["rejected"]["duplicate_video"] += 1
            continue
        if check_files and resolved is not None and not resolved.is_file():
            stats["rejected"]["missing_file"] += 1
            continue
        sequence_value = first_value(row, sequence_fields)
        sequence_id = str(sequence_value).strip() if sequence_value is not None else ""
        if not sequence_id:
            sequence_id = derive_sequence_id(video)
        sequence_id = f"{name}:{sequence_id}"
        candidates.append(
            {
                "video_path": video,
                "prompt": caption,
                "source_dataset": name,
                "source_sequence_id": sequence_id,
            }
        )
        seen_videos.add(video)

    candidates.sort(
        key=lambda row: stable_score(seed, name, row["source_sequence_id"], row["video_path"])
    )
    caption_counts: Counter[str] = Counter()
    filtered: list[dict[str, Any]] = []
    for row in candidates:
        caption_key = row["prompt"].casefold()
        if caption_counts[caption_key] >= max_caption_repeats:
            stats["rejected"]["repeated_caption"] += 1
            continue
        caption_counts[caption_key] += 1
        filtered.append(row)

    by_sequence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filtered:
        by_sequence[row["source_sequence_id"]].append(row)
    sequence_ids = sorted(
        by_sequence,
        key=lambda sequence_id: stable_score(seed, phase, name, sequence_id),
    )
    selected: list[dict[str, Any]] = []
    for sequence_id in sequence_ids:
        group = sorted(
            by_sequence[sequence_id],
            key=lambda row: stable_score(seed, phase, row["video_path"]),
        )
        remaining = quota - len(selected)
        if remaining <= 0:
            break
        selected.extend(group[:remaining])

    stats["selected"] = len(selected)
    stats["shortfall"] = max(0, quota - len(selected))
    stats["candidate_sequences"] = len(by_sequence)
    stats["selected_sequences"] = len({row["source_sequence_id"] for row in selected})
    stats["rejected"] = dict(sorted(stats["rejected"].items()))
    stats["status"] = "ok" if not stats["shortfall"] else "shortfall"
    if check_files and stats["rejected"].get("missing_file"):
        raise ManifestBuildError(
            f"Source {name!r} has {stats['rejected']['missing_file']} missing files. "
            "The phase was not frozen."
        )
    return selected, stats


def split_by_sequence(
    rows: list[dict[str, Any]], *, val_ratio: float, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_source_sequence: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        by_source_sequence[row["source_dataset"]][row["source_sequence_id"]].append(row)

    validation_sequences: set[str] = set()
    for source, groups in by_source_sequence.items():
        sequence_ids = sorted(
            groups,
            key=lambda sequence_id: stable_score(seed, "validation", source, sequence_id),
        )
        if val_ratio <= 0 or len(sequence_ids) < 2:
            count = 0
        else:
            count = max(1, round(len(sequence_ids) * val_ratio))
            count = min(count, len(sequence_ids) - 1)
        validation_sequences.update(sequence_ids[:count])

    train: list[dict[str, Any]] = []
    val: list[dict[str, Any]] = []
    for row in rows:
        destination = val if row["source_sequence_id"] in validation_sequences else train
        copied = dict(row)
        copied["split"] = "val" if destination is val else "train"
        destination.append(copied)
    train.sort(key=lambda row: stable_score(seed, "train", row["video_path"]))
    val.sort(key=lambda row: stable_score(seed, "val", row["video_path"]))
    return train, val


def enforce_source_fraction(rows: list[dict[str, Any]], maximum: float) -> None:
    counts = Counter(row["source_dataset"] for row in rows)
    total = len(rows)
    violations = {
        source: count / total
        for source, count in counts.items()
        if total and count / total > maximum + 1e-12
    }
    if violations:
        details = ", ".join(f"{name}={fraction:.1%}" for name, fraction in violations.items())
        raise ManifestBuildError(
            f"Configured source mix exceeds max_source_fraction={maximum:.1%}: {details}"
        )


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def write_diffsynth_csv(rows: list[dict[str, Any]], path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video", "prompt"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"video": row["video_path"], "prompt": row["prompt"]})
    os.replace(temporary, path)


def current_git_commit(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def git_worktree_dirty(project_root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return bool(result.stdout.strip())


def distribution(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    counts = Counter(row["source_dataset"] for row in rows)
    total = len(rows)
    return {
        source: {"count": count, "fraction": round(count / total, 6) if total else 0.0}
        for source, count in sorted(counts.items())
    }


def build(args: argparse.Namespace) -> dict[str, Path]:
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config_dir = config_path.parent
    project_root = Path(__file__).resolve().parents[1]
    seed = int(config.get("seed", 20260818))
    val_ratio = args.val_ratio if args.val_ratio is not None else float(config.get("val_ratio", 0.1))
    if not 0 <= val_ratio < 1:
        raise ManifestBuildError("val_ratio must satisfy 0 <= val_ratio < 1")
    dataset_base = expand_path(str(config["dataset_base_path"]), relative_to=config_dir)
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else project_root / "training_metadata" / "generated"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    quality = {
        "min_chars": 24,
        "max_chars": 420,
        "max_exact_caption_repeats": 4,
        "reject_patterns": [r"\bvideo[_ -]?id\s*:", r"\bfile(?:name)?\s*:"],
        **config.get("caption_quality", {}),
    }

    all_rows: list[dict[str, Any]] = []
    source_reports: dict[str, Any] = {}
    for source in config.get("sources", []):
        rows, stats = load_source(
            source,
            phase=args.phase,
            config_dir=config_dir,
            dataset_base=dataset_base,
            seed=seed,
            quality=quality,
            check_files=args.check_files,
            emit_relative_paths=bool(config.get("emit_relative_paths", True)),
        )
        all_rows.extend(rows)
        source_reports[str(source["name"])] = stats

    if not all_rows:
        raise ManifestBuildError(f"No usable rows were selected for phase {args.phase!r}")
    maximum = float(config.get("max_source_fraction", 0.30))
    enforce_source_fraction(all_rows, maximum)
    train, val = split_by_sequence(all_rows, val_ratio=val_ratio, seed=seed)
    if not train:
        raise ManifestBuildError("Training split is empty")
    enforce_source_fraction(train, maximum)

    train_sequences = {row["source_sequence_id"] for row in train}
    val_sequences = {row["source_sequence_id"] for row in val}
    leakage = sorted(train_sequences & val_sequences)
    if leakage:
        raise ManifestBuildError(f"Sequence leakage detected: {leakage[:5]}")

    prefix = f"unified_{args.phase}"
    outputs = {
        "train_jsonl": output_dir / f"{prefix}_train.jsonl",
        "val_jsonl": output_dir / f"{prefix}_val.jsonl",
        "train_csv": output_dir / f"{prefix}_train.csv",
        "val_csv": output_dir / f"{prefix}_val.csv",
        "report": output_dir / f"{prefix}_report.json",
    }
    write_jsonl(train, outputs["train_jsonl"])
    write_jsonl(val, outputs["val_jsonl"])
    write_diffsynth_csv(train, outputs["train_csv"])
    write_diffsynth_csv(val, outputs["val_csv"])

    report = {
        "schema_version": 1,
        "phase": args.phase,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "val_ratio": val_ratio,
        "dataset_base_path": str(dataset_base),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "project_git_commit": current_git_commit(project_root),
        "project_git_dirty": git_worktree_dirty(project_root),
        "check_files": args.check_files,
        "total_selected": len(all_rows),
        "train_count": len(train),
        "val_count": len(val),
        "sequence_leakage_count": len(leakage),
        "source_distribution_all": distribution(all_rows),
        "source_distribution_train": distribution(train),
        "source_distribution_val": distribution(val),
        "sources": source_reports,
        "outputs": {
            key: {"path": str(path), "sha256": sha256_file(path)}
            for key, path in outputs.items()
            if key != "report"
        },
    }
    outputs["report"].write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return outputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="JSON source specification")
    parser.add_argument("--phase", choices=("smoke", "pilot", "scale"), default="smoke")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--val-ratio", type=float, help="Override config validation ratio")
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Require every selected input video to exist before freezing outputs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        outputs = build(args)
    except (ManifestBuildError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Frozen phase: {args.phase}")
    for name, path in outputs.items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
