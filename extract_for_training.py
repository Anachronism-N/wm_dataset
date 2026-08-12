#!/usr/bin/env python3
"""
Extract videos from dataset archives and build Wan2.2 training manifests.

Supports:
  - HOIGen-1M: 10 zips, 106,100 videos, CSV captions
  - Seamless Interaction: 50 tars, 476 samples, transcript captions

Features:
  - Resumable: skips already-extracted videos
  - Atomic: writes to .part first, then renames
  - Wan2.2 format: {video_path, caption, source, resolution, fps, duration_sec, num_frames}
"""

import argparse
import csv
import json
import os
import re
import shutil
import tarfile
import zipfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional


def extract_zip_archive(archive_path: str, video_member: str, target_dir: Path) -> Optional[str]:
    """Extract a single video from a zip archive. Returns target path or None."""
    target = target_dir / Path(video_member).name
    if target.exists():
        with zipfile.ZipFile(archive_path) as zf:
            info = zf.getinfo(video_member)
            if target.stat().st_size == info.file_size:
                return str(target)
    with zipfile.ZipFile(archive_path) as zf:
        info = zf.getinfo(video_member)
        temporary = target.with_suffix(target.suffix + ".part")
        with zf.open(info) as source, temporary.open("wb") as dest:
            shutil.copyfileobj(source, dest, length=8 * 1024 * 1024)
        if temporary.stat().st_size != info.file_size:
            temporary.unlink(missing_ok=True)
            return None
        os.replace(temporary, target)
        return str(target)


def extract_tar_video(archive_path: str, video_member: str, target_dir: Path) -> Optional[str]:
    """Extract a single video from a tar archive. Returns target path or None."""
    target = target_dir / Path(video_member).name
    with tarfile.open(archive_path) as tf:
        member = tf.getmember(video_member)
        if target.exists() and target.stat().st_size == member.size:
            return str(target)
        temporary = target.with_suffix(target.suffix + ".part")
        extracted = tf.extractfile(member)
        if extracted is None:
            return None
        with temporary.open("wb") as dest:
            shutil.copyfileobj(extracted, dest, length=8 * 1024 * 1024)
        if temporary.stat().st_size != member.size:
            temporary.unlink(missing_ok=True)
            return None
        os.replace(temporary, target)
        return str(target)


def build_hoigen_training(args: argparse.Namespace) -> int:
    """Extract HOIGen-1M videos and build Wan2.2 training manifest."""
    args.video_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    with args.manifest.open(encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))

    # Group by archive for efficient extraction
    by_archive: dict[str, list[dict]] = {}
    for entry in entries:
        by_archive.setdefault(entry["archive_path"], []).append(entry)

    training_rows = []
    total = len(entries)
    extracted = 0
    failed = 0

    for archive_path, batch in sorted(by_archive.items()):
        archive = Path(archive_path)
        if not archive.exists():
            print(f"WARNING: archive not found: {archive_path}, skipping {len(batch)} entries")
            failed += len(batch)
            continue
        print(f"Processing {archive_path} ({len(batch)} videos)...")
        for entry in batch:
            video_path = extract_zip_archive(archive_path, entry["video_member"], args.video_dir)
            if video_path is None:
                failed += 1
                continue
            extracted += 1
            caption = entry.get("caption_detailed", "")
            if not caption and entry.get("caption_variants"):
                caption = entry["caption_variants"][0]
            training_rows.append({
                "video_path": video_path,
                "caption": caption,
                "source": "hoigen1m",
                "source_sequence_id": entry.get("source_sequence_id", ""),
                "width": entry.get("width"),
                "height": entry.get("height"),
                "fps": entry.get("fps"),
                "duration_sec": entry.get("duration_sec"),
                "num_frames": entry.get("num_frames"),
            })
            if extracted % 5000 == 0:
                print(f"  Progress: {extracted}/{total}, failed={failed}")

    # Write training manifest
    with open(args.output, "w", encoding="utf-8") as f:
        for row in sorted(training_rows, key=lambda r: r["video_path"]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nHOIGen-1M extraction complete:")
    print(f"  Total entries: {total}")
    print(f"  Extracted: {extracted}")
    print(f"  Failed: {failed}")
    print(f"  Training rows: {len(training_rows)}")
    print(f"  Output: {args.output}")
    return 0 if failed == 0 else 1


def build_seamless_training(args: argparse.Namespace) -> int:
    """Extract Seamless Interaction videos and build Wan2.2 training manifest."""
    args.video_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    with args.manifest.open(encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))

    by_archive: dict[str, list[dict]] = {}
    for entry in entries:
        by_archive.setdefault(entry["archive_path"], []).append(entry)

    training_rows = []
    total = len(entries)
    extracted = 0
    failed = 0
    no_transcript = 0

    for archive_path, batch in sorted(by_archive.items()):
        archive = Path(archive_path)
        if not archive.exists():
            print(f"WARNING: archive not found: {archive_path}, skipping {len(batch)} entries")
            failed += len(batch)
            continue
        print(f"Processing {archive_path} ({len(batch)} samples)...")
        for entry in batch:
            video_path = extract_tar_video(archive_path, entry["video_member"], args.video_dir)
            if video_path is None:
                failed += 1
                continue
            extracted += 1
            transcript = entry.get("transcript", "").strip()
            if not transcript:
                no_transcript += 1
                caption = "Two people interacting and having a conversation."
            else:
                caption = transcript
            training_rows.append({
                "video_path": video_path,
                "caption": caption,
                "source": "seamless_interaction",
                "source_sample_id": entry.get("sample_id", ""),
                "annotation_source": entry.get("annotation_source", ""),
            })

    with open(args.output, "w", encoding="utf-8") as f:
        for row in sorted(training_rows, key=lambda r: r["video_path"]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nSeamless Interaction extraction complete:")
    print(f"  Total entries: {total}")
    print(f"  Extracted: {extracted}")
    print(f"  Failed: {failed}")
    print(f"  No transcript: {no_transcript}")
    print(f"  Training rows: {len(training_rows)}")
    print(f"  Output: {args.output}")
    return 0 if failed == 0 else 1


def build_parser():
    parser = argparse.ArgumentParser(description="Extract videos and build Wan2.2 training manifests")
    subparsers = parser.add_subparsers(dest="dataset", required=True)

    hoigen = subparsers.add_parser("hoigen")
    hoigen.add_argument("--manifest", type=Path, required=True,
                        help="HOIGen-1M manifest JSONL")
    hoigen.add_argument("--video-dir", type=Path, required=True,
                        help="Target directory for extracted videos")
    hoigen.add_argument("--output", type=Path, required=True,
                        help="Wan2.2 training manifest output")
    hoigen.set_defaults(func=build_hoigen_training)

    seamless = subparsers.add_parser("seamless")
    seamless.add_argument("--manifest", type=Path, required=True,
                          help="Seamless Interaction manifest JSONL")
    seamless.add_argument("--video-dir", type=Path, required=True,
                          help="Target directory for extracted videos")
    seamless.add_argument("--output", type=Path, required=True,
                          help="Wan2.2 training manifest output")
    seamless.set_defaults(func=build_seamless_training)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))
