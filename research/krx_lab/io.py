"""해시와 원자적 산출물 쓰기."""

import hashlib
import json
import os
from pathlib import Path


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def source_hash():
    root = Path(__file__).parent
    return canonical_hash({p.name: digest(p) for p in sorted(root.glob("*.py"))})
