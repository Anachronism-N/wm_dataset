from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("build_unified_manifest", ROOT / "scripts" / "build_unified_manifest.py")
auditor = load_module("audit_experiment_manifest", ROOT / "scripts" / "audit_experiment_manifest.py")


class ExperimentManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.data = self.base / "data"
        self.data.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def make_source(self, name: str, groups: int = 8, clips_per_group: int = 2) -> Path:
        path = self.base / f"{name}.jsonl"
        rows = []
        for group in range(groups):
            for clip in range(clips_per_group):
                video = self.data / f"{name}_sequence{group}_{clip:03d}.mp4"
                video.write_bytes(b"test")
                rows.append(
                    {
                        "video_path": str(video),
                        "prompt": f"A person performs visible action number {group} and changes an object.",
                        "source_sequence_id": f"sequence-{group}",
                    }
                )
        rows.append(
            {
                "video_path": str(self.data / f"{name}_bad.mp4"),
                "prompt": f"A generic clip, video_id: {name}_bad",
                "source_sequence_id": "bad",
            }
        )
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        return path

    def make_config(self) -> Path:
        source_a = self.make_source("source_a")
        source_b = self.make_source("source_b")
        config = {
            "seed": 7,
            "dataset_base_path": str(self.data),
            "emit_relative_paths": True,
            "val_ratio": 0.25,
            "max_source_fraction": 0.6,
            "caption_quality": {
                "min_chars": 20,
                "max_chars": 200,
                "max_exact_caption_repeats": 4,
                "reject_patterns": [r"\bvideo_id\s*:"],
            },
            "sources": [
                {"name": "source_a", "manifest": str(source_a), "quotas": {"smoke": 12}},
                {"name": "source_b", "manifest": str(source_b), "quotas": {"smoke": 12}},
            ],
        }
        path = self.base / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_builder_is_deterministic_and_group_isolated(self):
        config = self.make_config()
        out_a = self.base / "out_a"
        out_b = self.base / "out_b"
        outputs_a = builder.build(
            argparse.Namespace(
                config=config,
                phase="smoke",
                output_dir=out_a,
                val_ratio=None,
                check_files=True,
            )
        )
        outputs_b = builder.build(
            argparse.Namespace(
                config=config,
                phase="smoke",
                output_dir=out_b,
                val_ratio=None,
                check_files=True,
            )
        )
        train_a = outputs_a["train_jsonl"].read_text(encoding="utf-8")
        val_a = outputs_a["val_jsonl"].read_text(encoding="utf-8")
        self.assertEqual(train_a, outputs_b["train_jsonl"].read_text(encoding="utf-8"))
        self.assertEqual(val_a, outputs_b["val_jsonl"].read_text(encoding="utf-8"))
        train_sequences = {json.loads(line)["source_sequence_id"] for line in train_a.splitlines()}
        val_sequences = {json.loads(line)["source_sequence_id"] for line in val_a.splitlines()}
        self.assertFalse(train_sequences & val_sequences)
        self.assertNotIn("video_id:", train_a + val_a)

        report, failures = auditor.audit(
            argparse.Namespace(
                train=outputs_a["train_jsonl"],
                val=outputs_a["val_jsonl"],
                base_path=self.data,
                check_files=True,
                min_caption_chars=20,
                max_source_fraction=0.6,
            )
        )
        self.assertFalse(failures)
        self.assertTrue(report["passed"])

    def test_auditor_rejects_sequence_leakage(self):
        train = self.base / "train.jsonl"
        val = self.base / "val.jsonl"
        common = {
            "video_path": "clip.mp4",
            "prompt": "A person reaches for a cup and places it on a table.",
            "source_dataset": "source",
            "source_sequence_id": "source:sequence-1",
        }
        train.write_text(json.dumps({**common, "split": "train"}) + "\n", encoding="utf-8")
        val.write_text(
            json.dumps({**common, "video_path": "clip2.mp4", "split": "val"}) + "\n",
            encoding="utf-8",
        )
        report, failures = auditor.audit(
            argparse.Namespace(
                train=train,
                val=val,
                base_path=None,
                check_files=False,
                min_caption_chars=20,
                max_source_fraction=1.0,
            )
        )
        self.assertTrue(failures)
        self.assertEqual(report["sequence_leakage_count"], 1)


if __name__ == "__main__":
    unittest.main()
