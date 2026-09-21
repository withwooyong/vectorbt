"""Regression checks for pinned v3 snapshot integrity; no database access."""
import csv
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab import v3_snapshot as v3


def h(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def test_actual_upstream_metadata_root():
    root = Path(__file__).resolve().parents[2]
    records = json.loads((root / 'docs/strategy-research/backtest-lab/postgresql-readiness-2026-09-21/metadata/results.json').read_text(encoding='utf-8'))
    checks = {r['check']: r['data'] for r in records}
    v3._validate_metadata(checks['revision'][0], checks['members'])
    checks['members'][0]['row_count'] += 1
    with pytest.raises(ValueError, match='aggregate hash'):
        v3._validate_metadata(checks['revision'][0], checks['members'])


def test_price_hash_is_day_hash_of_exact_postgres_text():
    values = ['{"adjusted": false, "stock_id": 1, "trading_date": "2014-01-02"}',
              '{"adjusted": true, "stock_id": 1, "trading_date": "2014-01-02"}',
              '{"adjusted": false, "stock_id": 1, "trading_date": "2014-01-03"}']
    member = v3._MemberHash('PRICE')
    for value in values:
        member.add(value)
    assert member.value() == h(h('\n'.join(values[:2])) + '\n' + h(values[2]))
    assert member.rows == 3
    assert member.value() == member.value()


def test_sql_is_read_only_and_fixed_scope():
    sql = v3.export_v3_sql()
    assert 'REPEATABLE READ READ ONLY' in sql
    assert 'ROLLBACK;' in sql
    assert '2024' not in sql
    assert 'INSERT ' not in sql and 'CREATE ' not in sql
    assert 'greatest(affected_from' in sql
    assert 'jsonb_build_array(payload_id,payload_sha256)' in sql
    for relation, _, _ in v3.SPECS.values():
        assert 'kiwoom.' + relation in sql


def fixture_stream(monkeypatch):
    rows = {kind: '{"stock_id": 1, "trading_date": "2014-01-02", "stock_code": "005930"}' for kind in v3.SPECS}
    rows['SOURCE_PAYLOAD'] = '[1, "payload-hash"]'
    members = []
    for kind, (relation, _, _) in v3.SPECS.items():
        hasher = v3._MemberHash(kind)
        hasher.add(rows[kind])
        members.append(dict(member_kind=kind, relation_name='kiwoom.' + relation, row_count=1,
                            content_sha256=hasher.value(), min_valid_date='2014-01-02',
                            max_valid_date='2014-01-02', max_source_record_id=None,
                            selection_predicate='fixture', revision_id=v3.REVISION_ID))
    root = v3._LinesHash()
    for m in sorted(members, key=lambda x: x['member_kind']):
        root.add(':'.join(str(m[f]) for f in ['member_kind', 'relation_name', 'row_count', 'min_valid_date',
                                            'max_valid_date', 'max_source_record_id', 'selection_predicate',
                                            'content_sha256'] if m[f] is not None))
    monkeypatch.setattr(v3, 'REVISION_SHA256', root.value())
    revision = dict(revision_id=v3.REVISION_ID, dataset_name=v3.DATASET_NAME,
                    revision_label=v3.REVISION_LABEL, content_sha256=root.value(), status='SEALED',
                    period_start=v3.PERIOD_START, period_end=v3.PERIOD_END)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['REVISION', json.dumps(revision)])
    for m in members:
        writer.writerow(['MEMBER', json.dumps(m)])
    for kind, row in rows.items():
        writer.writerow([kind, row])
    writer.writerow(['END', 'true'])
    stream.seek(0)
    return stream


def test_export_verify_and_load_without_db(tmp_path, monkeypatch):
    out = tmp_path / 'snapshot'
    v3.consume_v3_csv(fixture_stream(monkeypatch), out, v3.export_v3_sql(), chunk_rows=1)
    manifest = v3.verify_v3_snapshot(out)
    assert manifest['real_execution_admitted'] is False
    assert len(manifest['parts']) == len(v3.SPECS)
    tables = v3.load_v3_tables(out, ['PRICE', 'SOURCE_PAYLOAD'])
    assert tables['PRICE'].iloc[0].stock_code == '005930'
    assert list(tables['SOURCE_PAYLOAD'].columns) == ['payload_id', 'payload_sha256']
    with pytest.raises(FileExistsError):
        v3.consume_v3_csv(fixture_stream(monkeypatch), out, v3.export_v3_sql())


def test_truncation_never_completes(tmp_path, monkeypatch):
    stream = fixture_stream(monkeypatch)
    value = stream.getvalue().rsplit('END,', 1)[0]
    with pytest.raises(ValueError, match='Missing export end marker'):
        v3.consume_v3_csv(io.StringIO(value), tmp_path / 'snapshot', v3.export_v3_sql())
    assert v3.read_json(tmp_path / 'snapshot/manifest.json')['status'] == 'FAILED'


def test_rehashed_parquet_tampering_still_fails_member_hash(tmp_path, monkeypatch):
    out = tmp_path / 'snapshot'
    v3.consume_v3_csv(fixture_stream(monkeypatch), out, v3.export_v3_sql())
    manifest = v3.read_json(out / 'manifest.json')
    part = manifest['parts'][0]
    frame = pd.read_parquet(out / part['file'])
    frame.loc[0, 'pg_json'] = frame.loc[0, 'pg_json'].replace('005930', '000660')
    frame.to_parquet(out / part['file'], index=False)
    part['sha256'] = v3.digest(out / part['file'])
    v3.write_json(out / 'manifest.json', manifest)
    with pytest.raises(ValueError, match='Member content mismatch'):
        v3.verify_v3_snapshot(out)


def test_path_escape_rejected(tmp_path, monkeypatch):
    out = tmp_path / 'snapshot'
    v3.consume_v3_csv(fixture_stream(monkeypatch), out, v3.export_v3_sql())
    manifest = v3.read_json(out / 'manifest.json')
    manifest['parts'][0]['file'] = '../outside.parquet'
    v3.write_json(out / 'manifest.json', manifest)
    with pytest.raises(ValueError, match='path escaped'):
        v3.verify_v3_snapshot(out)


@pytest.mark.parametrize('exit_code', [0, 2])
def test_live_process_exit_controls_completion(tmp_path, monkeypatch, exit_code):
    import sys
    stream = fixture_stream(monkeypatch)
    replay = tmp_path / 'stream.csv'
    replay.write_bytes(stream.getvalue().encode('utf-8'))
    command = [sys.executable, '-c',
               'import sys; sys.stdout.buffer.write(open(sys.argv[1], "rb").read()); sys.exit(int(sys.argv[2]))',
               str(replay), str(exit_code)]
    out = tmp_path / 'snapshot'
    if exit_code:
        with pytest.raises(RuntimeError, match='extraction failed'):
            v3.extract_v3(out, command=command)
        assert v3.read_json(out / 'manifest.json')['status'] == 'FAILED'
        with pytest.raises(ValueError, match='incomplete'):
            v3.verify_v3_snapshot(out)
    else:
        v3.extract_v3(out, command=command)
        v3.verify_v3_snapshot(out)
        frames = list(v3.iter_v3_frames(out, 'PRICE', columns=['stock_code'], verify=False))
        assert list(frames[0].columns) == ['stock_code']
