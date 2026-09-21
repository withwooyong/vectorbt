"""Read-only v3 export with upstream PostgreSQL-text member hash verification.

This establishes snapshot integrity, never REAL execution admission. The exact
PostgreSQL JSON text is retained because Python JSON serialization is not the
upstream sealing format. All members are read in one repeatable-read transaction.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess

import pandas as pd

from .io import digest, read_json, write_json
from .source_contract_admission import (
    DATASET_NAME, REVISION_ID, REVISION_LABEL, REVISION_SHA256, PERIOD_START, PERIOD_END,
)

# Predicates and ordering mirror ted-startup/scripts/data_delivery/seal_backtest_dataset_revision.py.
DAY = "trading_date BETWEEN '2014-01-01' AND '2023-12-31'"
SPECS = {
    'PRICE': ('backtest_price_v2', DAY, 'trading_date,stock_id,adjusted'),
    'UNIVERSE': ('backtest_universe_v2', "security_type='COMMON_STOCK' AND valid_from<='2023-12-31' AND valid_to>='2014-01-01'", 'stock_id,market,valid_from'),
    'IDENTIFIER': ('instrument_identifier_history', "valid_from<='2023-12-31' AND valid_to>='2014-01-01'", 'stock_id,identifier_type,identifier_value,valid_from'),
    'CALENDAR': ('market_calendar', "market='KRX' AND " + DAY, 'market,trading_date'),
    'BENCHMARK': ('benchmark_daily', DAY, 'benchmark_code,trading_date'),
    'STATUS': ('backtest_status_v2', DAY, 'stock_id,trading_date'),
    'CORPORATE_ACTION': ('backtest_corporate_action_v2', "effective_date BETWEEN '2014-01-01' AND '2023-12-31'", 'event_id'),
    'ADJUSTMENT': ('backtest_adjustment_v2', DAY, 'stock_id,trading_date,event_id'),
    'EXECUTION_RULE': ('backtest_execution_rule_v2', "effective_from<='2023-12-31' AND effective_to>='2014-01-01'", 'rule_kind,market,effective_from'),
    'ADMISSION_ISSUE': ('backtest_admission_issue_v2', "affected_from<='2023-12-31' AND affected_to>='2014-01-01'", 'issue_code,affected_from,to_jsonb(x)::text'),
    'SOURCE_PAYLOAD': ('source_payload', "EXISTS (SELECT 1 FROM kiwoom.source_record r WHERE r.payload_id=x.payload_id AND r.valid_from BETWEEN '2014-01-01' AND '2023-12-31')", 'payload_id'),
}
COMMAND = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'home',
           'docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db psql -X -q -U kiwoom -d kiwoom_db']


def export_v3_sql():
    """Fixed-scope SQL; no caller-provided identifiers, dates or predicates."""
    queries = [f"SELECT 'REVISION',to_jsonb(x)::text FROM kiwoom.dataset_revision x WHERE revision_id='{REVISION_ID}'",
               f"SELECT 'MEMBER',to_jsonb(x)::text FROM kiwoom.dataset_revision_member x WHERE revision_id='{REVISION_ID}' ORDER BY member_kind"]
    for kind, (relation, predicate, order) in SPECS.items():
        source = f'kiwoom.{relation} x'
        expression = 'to_jsonb(x)::text'
        if kind == 'SOURCE_PAYLOAD':
            expression = 'jsonb_build_array(payload_id,payload_sha256)::text'
        if kind == 'ADMISSION_ISSUE':
            source = ("(SELECT issue_code,severity,affected_scope,"
                      "greatest(affected_from,'2014-01-01'::date) affected_from,"
                      "least(affected_to,'2023-12-31'::date) affected_to,decision,details "
                      f'FROM kiwoom.{relation} WHERE {predicate}) x')
            predicate = 'TRUE'
        queries.append(f"SELECT '{kind}',{expression} FROM {source} WHERE {predicate} ORDER BY {order}")
    return ("\\set ON_ERROR_STOP on\nBEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n"
            "SET LOCAL statement_timeout='1800s';\nSET LOCAL lock_timeout='3s';\n" +
            ''.join(f"COPY ({query}) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8');\n" for query in queries) +
            "COPY (SELECT 'END','true') TO STDOUT WITH (FORMAT CSV);\nROLLBACK;\n")


class _LinesHash:
    def __init__(self):
        self.hash = hashlib.sha256()
        self.count = 0

    def add(self, text):
        if self.count:
            self.hash.update(b'\n')
        self.hash.update(text.encode('utf-8'))
        self.count += 1

    def value(self):
        return self.hash.hexdigest() if self.count else None


class _MemberHash:
    def __init__(self, kind):
        self.kind = kind
        self.total = _LinesHash()
        self.day = _LinesHash()
        self.last_date = None
        self.rows = 0

    def add(self, text):
        self.rows += 1
        if self.kind != 'PRICE':
            self.total.add(text)
            return
        day = json.loads(text)['trading_date']
        if self.last_date and day < self.last_date:
            raise ValueError('PRICE date order invalid')
        if self.last_date != day:
            if self.last_date is not None:
                self.total.add(self.day.value())
            self.day = _LinesHash()
            self.last_date = day
        self.day.add(text)

    def value(self):
        if self.kind == 'PRICE' and self.last_date is not None:
            result = self.total.hash.copy()
            if self.total.count:
                result.update(b'\n')
            result.update(self.day.value().encode('ascii'))
            return result.hexdigest()
        return self.total.value()


def _validate_metadata(revision, members):
    for field, expected in {'revision_id': REVISION_ID, 'dataset_name': DATASET_NAME,
                            'revision_label': REVISION_LABEL, 'content_sha256': REVISION_SHA256,
                            'status': 'SEALED', 'period_start': PERIOD_START, 'period_end': PERIOD_END}.items():
        if revision.get(field) != expected:
            raise ValueError(f'Revision binding mismatch: {field}')
    if len(members) != len(SPECS) or {m['member_kind'] for m in members} != set(SPECS):
        raise ValueError('Incomplete or duplicate revision members')
    root = _LinesHash()
    for member in sorted(members, key=lambda m: (m['member_kind'], m['relation_name'])):
        kind = member['member_kind']
        if member['revision_id'] != REVISION_ID or member['relation_name'] != 'kiwoom.' + SPECS[kind][0]:
            raise ValueError('Member binding mismatch')
        fields = ['member_kind', 'relation_name', 'row_count', 'min_valid_date', 'max_valid_date',
                  'max_source_record_id', 'selection_predicate', 'content_sha256']
        root.add(':'.join(str(member[f]) for f in fields if member[f] is not None))
    if root.value() != REVISION_SHA256:
        raise ValueError('Revision member aggregate hash mismatch')


def _check_members(members, hashes):
    for member in members:
        actual = hashes[member['member_kind']]
        if actual.rows != member['row_count'] or actual.value() != member['content_sha256']:
            raise ValueError(f"Member content mismatch: {member['member_kind']}")


def consume_v3_csv(stream, out, sql, chunk_rows=100000, *, finalize=True):
    """Consume an export stream into a new directory; failures never become COMPLETE.

    Public for offline replay/testing. Call extract_v3 for a live authenticated
    SSH export. Live extraction sets finalize=False until its process succeeds.
    """
    if chunk_rows < 1:
        raise ValueError('chunk_rows must be positive')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'extract.sql').write_text(sql, encoding='utf-8')
    manifest = dict(schema_version='v3-snapshot-1', status='EXTRACTING', source='REAL',
                    real_execution_admitted=False, parts=[], sql_sha256=digest(out / 'extract.sql'))
    write_json(out / 'manifest.json', manifest)
    hashes = {kind: _MemberHash(kind) for kind in SPECS}
    members, revision, pending, pending_kind = [], None, [], None

    def flush():
        if not pending:
            return
        filename = f'{pending_kind.lower()}-{len(manifest["parts"]):05d}.parquet'
        pd.DataFrame({'pg_json': pending}).to_parquet(out / filename, index=False)
        manifest['parts'].append(dict(file=filename, member_kind=pending_kind, rows=len(pending),
                                      sha256=digest(out / filename)))
        pending.clear()

    try:
        ended = False
        for kind, value in csv.reader(stream):
            if ended:
                raise ValueError('Data after end marker')
            if kind == 'REVISION':
                if revision is not None:
                    raise ValueError('Duplicate revision')
                revision = json.loads(value)
            elif kind == 'MEMBER':
                members.append(json.loads(value))
            elif kind == 'END':
                if value != 'true':
                    raise ValueError('Invalid end marker')
                ended = True
            else:
                if kind not in SPECS:
                    raise ValueError('Unknown member')
                if pending_kind != kind:
                    flush()
                    pending_kind = kind
                hashes[kind].add(value)
                pending.append(value)
                if len(pending) >= chunk_rows:
                    flush()
        flush()
        if not ended:
            raise ValueError('Missing export end marker')
        _validate_metadata(revision or {}, members)
        _check_members(members, hashes)
        manifest.update(status='COMPLETE' if finalize else 'VERIFYING_PROCESS', revision=revision, members=members,
                        dataset_name=DATASET_NAME, revision_id=REVISION_ID, revision_label=REVISION_LABEL,
                        revision_content_sha256=REVISION_SHA256, revision_status='SEALED',
                        period_start=PERIOD_START, period_end=PERIOD_END)
        write_json(out / 'manifest.json', manifest)
        return manifest
    except Exception as exc:
        manifest.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
        write_json(out / 'manifest.json', manifest)
        raise


def extract_v3(out, command=None, chunk_rows=100000):
    """Export fixed v3 scope via read-only SSH; never overwrite an existing path."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    sql = export_v3_sql()
    # A file-backed stdin avoids pipe deadlock while large COPY output streams.
    import tempfile
    with tempfile.TemporaryFile() as errors, tempfile.TemporaryFile() as query:
        query.write(sql.encode('utf-8'))
        query.seek(0)
        process = subprocess.Popen(command or COMMAND, stdin=query, stdout=subprocess.PIPE, stderr=errors)
        try:
            result = consume_v3_csv(io.TextIOWrapper(process.stdout, encoding='utf-8'), out, sql,
                                    chunk_rows, finalize=False)
            if process.wait(timeout=30) != 0:
                raise RuntimeError('SSH/psql extraction failed')
            result['status'] = 'COMPLETE'
            write_json(out / 'manifest.json', result)
            return result
        except Exception as exc:
            if (out / 'manifest.json').exists():
                manifest = read_json(out / 'manifest.json')
                manifest.update(status='FAILED', error=str(exc))
                write_json(out / 'manifest.json', manifest)
            raise
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if out.exists():
                errors.seek(0)
                (out / 'extract.stderr.txt').write_bytes(errors.read())


def verify_v3_snapshot(path):
    """Recompute local member counts/content against the pinned upstream seal."""
    path = Path(path)
    manifest = read_json(path / 'manifest.json')
    if manifest.get('status') != 'COMPLETE' or manifest.get('schema_version') != 'v3-snapshot-1':
        raise ValueError('Snapshot incomplete or unsupported')
    _validate_metadata(manifest['revision'], manifest['members'])
    _validate_manifest(manifest)
    if digest(path / 'extract.sql') != manifest['sql_sha256'] or (path / 'extract.sql').read_text(encoding='utf-8') != export_v3_sql():
        raise ValueError('SQL provenance mismatch')
    hashes = {kind: _MemberHash(kind) for kind in SPECS}
    seen = set()
    for part in manifest['parts']:
        target = path / part['file']
        if target.resolve().parent != path.resolve() or part['file'] in seen or digest(target) != part['sha256']:
            raise ValueError('Snapshot part corrupted or path escaped')
        seen.add(part['file'])
        frame = pd.read_parquet(target, columns=['pg_json'])
        if len(frame) != part['rows']:
            raise ValueError('Part row count mismatch')
        for value in frame.pg_json:
            hashes[part['member_kind']].add(value)
    _check_members(manifest['members'], hashes)
    return manifest


def _validate_manifest(manifest):
    expected = dict(schema_version='v3-snapshot-1', status='COMPLETE', source='REAL',
                    real_execution_admitted=False, dataset_name=DATASET_NAME, revision_id=REVISION_ID,
                    revision_label=REVISION_LABEL, revision_content_sha256=REVISION_SHA256,
                    revision_status='SEALED', period_start=PERIOD_START, period_end=PERIOD_END)
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError('Snapshot manifest binding mismatch')


def iter_v3_frames(path, kind, *, columns=None, verify=True):
    """Yield bounded source-column frames for memory-efficient adapter conversion."""
    path = Path(path)
    manifest = verify_v3_snapshot(path) if verify else read_json(path / 'manifest.json')
    _validate_manifest(manifest)
    if kind not in SPECS:
        raise ValueError('Unknown requested member')
    for part in manifest['parts']:
        if part['member_kind'] != kind:
            continue
        target = path / part['file']
        if target.resolve().parent != path.resolve():
            raise ValueError('Snapshot path escaped')
        rows = pd.read_parquet(target, columns=['pg_json']).pg_json.map(json.loads).tolist()
        frame = (pd.DataFrame(rows, columns=['payload_id', 'payload_sha256'])
                 if kind == 'SOURCE_PAYLOAD' else pd.DataFrame(rows))
        yield frame if columns is None else frame[list(columns)]


def load_v3_tables(path, kinds=None, *, verify=True):
    """Load original source columns. Caller controls kinds to avoid unwanted RAM use.

    verify=False is intended only after verify_v3_snapshot in the same trusted run.
    SOURCE_PAYLOAD consists of two-column arrays, matching the upstream seal.
    """
    path = Path(path)
    manifest = verify_v3_snapshot(path) if verify else read_json(path / 'manifest.json')
    _validate_manifest(manifest)
    requested = set(SPECS if kinds is None else kinds)
    if requested - set(SPECS):
        raise ValueError('Unknown requested member')
    result = {}
    for kind in requested:
        frames = list(iter_v3_frames(path, kind, verify=False))
        result[kind] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return result
