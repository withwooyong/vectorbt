"""SQLite 실행/시도 이력과 단일 worker 잠금."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import sqlite3

import psutil

from .io import read_json


def now():
    return datetime.now(timezone.utc).isoformat()


class Registry:
    def __init__(self, path):
        self.path = Path(path)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
              run_id TEXT PRIMARY KEY, spec TEXT NOT NULL, status TEXT NOT NULL,
              attempt INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
              reason TEXT, metrics TEXT, artifacts TEXT);
            CREATE TABLE IF NOT EXISTS attempts (
              run_id TEXT NOT NULL, attempt INTEGER NOT NULL, started_at TEXT NOT NULL,
              finished_at TEXT, status TEXT NOT NULL, reason TEXT, artifacts TEXT,
              PRIMARY KEY (run_id, attempt));
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def add(self, run_id, spec, status="PLANNED", reason=None):
        self.add_many([(run_id, spec, status, reason)])

    def add_many(self, rows):
        with self.connect() as db:
            timestamp = now()
            db.executemany("INSERT INTO runs(run_id,spec,status,updated_at,reason) VALUES(?,?,?,?,?)",
                           [(run_id, json.dumps(spec), status, timestamp, reason)
                            for run_id, spec, status, reason in rows])

    def block_many(self, records, reason):
        with self.connect() as db:
            timestamp = now()
            for record in records:
                attempt = record["attempt"] + 1
                db.execute("UPDATE runs SET status='BLOCKED',attempt=?,updated_at=?,reason=? WHERE run_id=?",
                           (attempt, timestamp, reason, record["run_id"]))
                db.execute("INSERT INTO attempts(run_id,attempt,started_at,finished_at,status,reason) "
                           "VALUES(?,?,?,?,'BLOCKED',?)", (record["run_id"], attempt, timestamp, timestamp, reason))

    def records(self):
        with self.connect() as db:
            return [{**json.loads(row["spec"]), **{k: row[k] for k in
                     ("run_id", "status", "attempt", "updated_at", "reason", "artifacts")},
                     "metrics": json.loads(row["metrics"]) if row["metrics"] else {}}
                    for row in db.execute("SELECT * FROM runs ORDER BY rowid")]

    def begin(self, run_id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT attempt,status FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row or row["status"] in ("SUCCEEDED", "RUNNING"):
                raise ValueError("실행 중/완료 run 재사용 오류")
            attempt = row["attempt"] + 1
            db.execute("UPDATE runs SET status='RUNNING',attempt=?,updated_at=?,reason=NULL WHERE run_id=?",
                       (attempt, now(), run_id))
            db.execute("INSERT INTO attempts(run_id,attempt,started_at,status) VALUES(?,?,?,'RUNNING')",
                       (run_id, attempt, now()))
            return attempt

    def finish(self, run_id, status, *, reason=None, metrics=None, artifacts=None):
        with self.connect() as db:
            db.execute("UPDATE runs SET status=?,updated_at=?,reason=?,metrics=?,artifacts=? WHERE run_id=?",
                       (status, now(), reason, json.dumps(metrics, allow_nan=False) if metrics is not None else None,
                        str(artifacts) if artifacts else None, run_id))
            db.execute("UPDATE attempts SET finished_at=?,status=?,reason=?,artifacts=? "
                       "WHERE run_id=? AND attempt=(SELECT attempt FROM runs WHERE run_id=?)",
                       (now(), status, reason, str(artifacts) if artifacts else None, run_id, run_id))

    def recover(self):
        # Caller must own the experiment process lock. Old attempts remain auditable.
        for row in self.records():
            if row["status"] == "RUNNING":
                self.finish(row["run_id"], "INTERRUPTED", reason="PREVIOUS_WORKER_EXITED")


@contextmanager
def worker_lock(out):
    lock = Path(out) / "worker.lock"
    payload = {"pid": os.getpid(), "host": socket.gethostname(),
               "create_time": psutil.Process().create_time()}
    if lock.exists():
        previous = read_json(lock)
        if previous["host"] != payload["host"]:
            raise RuntimeError("다른 호스트의 worker 잠금: 확인 없이 잠금을 해제하지 않습니다")
        try:
            active = psutil.Process(previous["pid"]).create_time() == previous["create_time"]
        except psutil.NoSuchProcess:
            active = False
        if active:
            raise RuntimeError("이 실험을 실행 중인 worker가 있습니다")
        lock.unlink()
    descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
        yield
    finally:
        lock.unlink(missing_ok=True)
