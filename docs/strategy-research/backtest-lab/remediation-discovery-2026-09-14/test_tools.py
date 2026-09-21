"""Offline regressions for evidence integrity, holdout boundaries and collection failure records."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import build_sample_request as builder
import collect_samples
import collect_server_metadata as server


ROOT = Path(__file__).resolve().parent


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "evidence"
        shutil.copytree(ROOT / "evidence" / "samples", self.path)

    def update_results_hash(self, data):
        target = self.path / "results.json"
        target.write_text(json.dumps(data), encoding="utf-8")
        receipt = json.loads((self.path / "receipt.json").read_text(encoding="utf-8"))
        receipt["evidence_sha256"]["results.json"] = hashlib.sha256(target.read_bytes()).hexdigest()
        (self.path / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    def test_saved_request_is_reproducible(self):
        expected = json.loads((ROOT / "sample-request.json").read_text(encoding="utf-8"))
        self.assertEqual(builder.build(self.path), expected)
        self.assertEqual(expected["sample_count"], len(expected["samples"]))

    def test_corrupt_evidence_rejected(self):
        with (self.path / "results.json").open("ab") as file:
            file.write(b" ")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            builder.build(self.path)

    def test_holdout_sample_rejected_even_with_updated_hash(self):
        data = json.loads((self.path / "results.json").read_text(encoding="utf-8"))
        next(r for r in data if r["check"] == "krx_fixed_samples")["data"][0]["trading_date"] = "2024-01-02"
        self.update_results_hash(data)
        with self.assertRaisesRegex(ValueError, "approved price scope"):
            builder.build(self.path)

    def test_duplicate_sample_rejected(self):
        data = json.loads((self.path / "results.json").read_text(encoding="utf-8"))
        samples = next(r for r in data if r["check"] == "krx_fixed_samples")["data"]
        samples.append(samples[0].copy())
        self.update_results_hash(data)
        with self.assertRaisesRegex(ValueError, "Duplicate sample"):
            builder.build(self.path)


class CollectorTests(unittest.TestCase):
    def test_sample_timeout_preserves_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "new"
            with patch.object(collect_samples.subprocess, "run", side_effect=subprocess.TimeoutExpired("ssh", 300)):
                with self.assertRaises(subprocess.TimeoutExpired):
                    collect_samples.collect(out)
            receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "FAILED")
            self.assertTrue((out / "query.sql").exists())
            self.assertIn("stdout.txt", receipt["evidence_sha256"])

    def test_metadata_timeout_preserves_partial_output_and_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "new"
            failure = subprocess.TimeoutExpired("ssh", 45, output=b"partial metadata", stderr=b"timeout diagnostic")
            with patch.object(server.subprocess, "run", side_effect=failure), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    server.collect(out, ["containers"])
            rows = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["error"], "TimeoutExpired")
            self.assertEqual((out / "containers.stdout.txt").read_bytes(), b"partial metadata")

    def test_metadata_nonzero_exit_is_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "new"
            result = subprocess.CompletedProcess("ssh", 1, b"", b"not available")
            with patch.object(server.subprocess, "run", return_value=result), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    server.collect(out, ["containers"])
            rows = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["returncode"], 1)

    def test_existing_output_not_modified(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            keep = out / "receipt.json"
            keep.write_bytes(b"user data")
            with patch.object(subprocess, "run") as run:
                for function in (collect_samples.collect, server.collect):
                    with self.assertRaises(FileExistsError):
                        function(out)
                run.assert_not_called()
            self.assertEqual(keep.read_bytes(), b"user data")


if __name__ == "__main__":
    unittest.main()
