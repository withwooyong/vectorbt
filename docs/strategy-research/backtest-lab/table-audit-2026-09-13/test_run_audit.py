"""Offline regression tests for audit parsing and durable failure evidence."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("table_audit_runner", Path(__file__).with_name("run_audit.py"))
audit_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_runner)


def output(*extra, read_only="on", complete=True):
    rows = [{"check": "context", "data": {"read_only": read_only}}, *extra]
    if complete is not None:
        rows.append({"check": "audit_complete", "data": complete})
    return "\n".join(json.dumps(row) for row in rows)


class ParseOutputTests(unittest.TestCase):
    def test_multiline_composite_json_and_unicode(self):
        raw = ('  \n{"check":"context","data":{"read_only":"on"}}\n'
               '{"check":"tables","data":[{"table":"stock"},\n {"table":"종목"}]}\n'
               '{"check":"audit_complete","data":true}\n')
        records = audit_runner.parse_output(raw)
        self.assertEqual(records[1]["data"], [{"table": "stock"}, {"table": "종목"}])
        self.assertEqual(len(records), 3)

    def test_malformed_json_rejected(self):
        with self.assertRaises(ValueError):
            audit_runner.parse_output(output() + '\n{"check":')

    def test_read_only_off_rejected(self):
        with self.assertRaises(ValueError):
            audit_runner.parse_output(output(read_only="off"))

    def test_missing_completion_rejected(self):
        with self.assertRaises(ValueError):
            audit_runner.parse_output(output(complete=None))

    def test_false_completion_rejected(self):
        with self.assertRaises(ValueError):
            audit_runner.parse_output(output(complete=False))

    def test_duplicate_check_ids_rejected(self):
        with self.assertRaises(ValueError):
            audit_runner.parse_output(output({"check": "context", "data": {"read_only": "on"}}))


class RunEvidenceTests(unittest.TestCase):
    def assert_failure_evidence(self, out, error_name):
        receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAILED")
        self.assertIn(error_name, receipt["error"])
        self.assertIn("finished_at", receipt)
        self.assertGreaterEqual(receipt["elapsed_seconds"], 0)
        self.assertEqual(receipt["sql_sha256"], hashlib.sha256((out / "query.sql").read_bytes()).hexdigest())
        self.assertEqual((out / "stdout.txt").read_bytes(), b"partial stdout\n")
        self.assertEqual((out / "stderr.txt").read_bytes(), b"database diagnostic\n")
        self.assertFalse((out / "results.json").exists())
        for name in ("stdout.txt", "stderr.txt"):
            self.assertEqual(receipt["evidence_sha256"][name], hashlib.sha256((out / name).read_bytes()).hexdigest())
        return receipt

    def test_nonzero_process_preserves_evidence(self):
        def failure(command, **kwargs):
            kwargs["stdout"].write(b"partial stdout\n")
            kwargs["stderr"].write(b"database diagnostic\n")
            return subprocess.CompletedProcess(command, 2)

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "new"
            with patch.object(audit_runner.subprocess, "run", side_effect=failure) as process:
                with self.assertRaises(RuntimeError):
                    audit_runner.run("inventory", out)
            process.assert_called_once()
            self.assertEqual(self.assert_failure_evidence(out, "RuntimeError")["returncode"], 2)

    def test_timeout_preserves_evidence(self):
        def timeout(command, **kwargs):
            kwargs["stdout"].write(b"partial stdout\n")
            kwargs["stderr"].write(b"database diagnostic\n")
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "new"
            with patch.object(audit_runner.subprocess, "run", side_effect=timeout):
                with self.assertRaises(subprocess.TimeoutExpired):
                    audit_runner.run("inventory", out)
            self.assert_failure_evidence(out, "TimeoutExpired")

    def test_existing_directory_refused_without_touching_files(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            existing = out / "query.sql"
            existing.write_bytes(b"preserve user evidence")
            with patch.object(audit_runner.subprocess, "run") as process:
                with self.assertRaises(FileExistsError):
                    audit_runner.run("inventory", out)
            process.assert_not_called()
            self.assertEqual(existing.read_bytes(), b"preserve user evidence")
            self.assertEqual({p.name for p in out.iterdir()}, {"query.sql"})


if __name__ == "__main__":
    unittest.main()
