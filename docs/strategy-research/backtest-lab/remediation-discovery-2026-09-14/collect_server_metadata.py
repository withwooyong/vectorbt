"""Capture an allowlist of deployed code/package/log metadata; never inspect environment values."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


COMMANDS = {
    "containers": "docker ps --format '{{.Names}} {{.Status}}'",
    "collector_location": "docker inspect kiwoom-app --format '{{index .Config.Labels \"com.docker.compose.project.working_dir\"}}'",
    "collector_image": "docker inspect kiwoom-app --format '{{.Image}}'",
    "package_versions": "docker exec kiwoom-app python -c 'import importlib.metadata as m; "
                        "print({p:m.version(p) for p in [\"pykrx\",\"pandas\",\"numpy\"]}); "
                        "print(m.distribution(\"pykrx\").locate_file(\"pykrx\"))'",
    "code_hashes": "docker exec kiwoom-app sha256sum "
                   "/app/app/adapter/out/krx/client.py /app/app/adapter/out/krx/mapper.py "
                   "/app/app/adapter/out/kiwoom/chart.py /app/scripts/backfill_delisted.py",
    "log_metadata": "stat --format='%n %s %y' /home/ted/backfill-phase1.log "
                    "/home/ted/backfill-phase2-pilot.log /home/ted/backfill-phase2.log && "
                    "sha256sum /home/ted/backfill-phase1.log /home/ted/backfill-phase2-pilot.log /home/ted/backfill-phase2.log",
    "repository_state": "git -C /srv/ted-startup rev-parse HEAD && git -C /srv/ted-startup status --short",
    "log_inventory": "find /srv/ted-startup -maxdepth 4 -type f -name '*.log' && "
                     "find /home/ted -maxdepth 1 -type f -name '*delist*'",
    "original_backfill_log": "if test -f /tmp/backfill_delisted.log; then "
                             "stat --format='%n %s %y' /tmp/backfill_delisted.log && "
                             "sha256sum /tmp/backfill_delisted.log && "
                             "head -n 4 /tmp/backfill_delisted.log && tail -n 12 /tmp/backfill_delisted.log; "
                             "else printf 'NOT_FOUND /tmp/backfill_delisted.log\n'; fi",
    "container_backfill_log": "docker exec kiwoom-app sh -c '"
                              "stat /tmp/backfill_delisted.log && sha256sum /tmp/backfill_delisted.log && "
                              "head -n 5 /tmp/backfill_delisted.log && tail -n 14 /tmp/backfill_delisted.log'",
    "container_backfill_log_full": "docker exec kiwoom-app cat /tmp/backfill_delisted.log",
}


def collect(out, selected=None):
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    for name, command in COMMANDS.items():
        if selected and name not in selected:
            continue
        argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home", command]
        error = None
        try:
            result = subprocess.run(argv, capture_output=True, timeout=45, check=False)
        except (subprocess.TimeoutExpired, OSError) as exc:
            error = type(exc).__name__
            result = subprocess.CompletedProcess(argv, -1, getattr(exc, "stdout", None) or b"",
                                                 getattr(exc, "stderr", None) or str(exc).encode("utf-8"))
        for suffix, content in (("stdout.txt", result.stdout), ("stderr.txt", result.stderr)):
            (out / f"{name}.{suffix}").write_bytes(content)
        receipts.append({"name": name, "command": command, "observed_at": datetime.now(timezone.utc).isoformat(),
                         "error": error,
                         "returncode": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                         "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()})
        preview = result.stdout.decode("utf-8", errors="replace").strip()
        print(name, result.returncode, preview[:1600], "[saved full output]" if len(preview) > 1600 else "")
        (out / "receipt.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if any(row["returncode"] != 0 for row in receipts):
        raise RuntimeError("One or more metadata checks failed; inspect receipt and stderr")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", nargs="+", choices=COMMANDS, help="Optional subset of allowlisted checks")
    args = parser.parse_args()
    collect(args.out, args.only)
