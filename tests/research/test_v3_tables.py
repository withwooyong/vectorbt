"""Typed-cache regressions, isolated from live PostgreSQL."""
from decimal import Decimal
import json

import pandas as pd
import pyarrow.parquet as pq
import pytest

from research.krx_lab import v3_tables as typed
from research.krx_lab.io import digest, read_json, write_json


def source_fixture(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    # The source verifier is tested separately against the actual pinned seal.
    # This fixture isolates transformation while preserving exact JSON numerics.
    rows = [
        '{"stock_code":"005930","stock_id":1,"trade_amount":null,"n":1.12345678901234567890,"mixed":"abc","nested":{"x":1},"flag":true}',
        '{"stock_code":"000660","stock_id":2,"trade_amount":42,"n":2,"mixed":3,"nested":{"y":[1,null]},"flag":null,"late":"value"}',
        '{"stock_code":"000001","stock_id":3,"trade_amount":null,"n":null,"mixed":null,"nested":null,"flag":false}'
    ]
    parts = []
    for index, row in enumerate(rows):
        filename = f'price-{index}.parquet'
        pd.DataFrame({'pg_json': [row]}).to_parquet(source / filename, index=False)
        parts.append(dict(file=filename, member_kind='PRICE', rows=1, sha256=digest(source / filename)))
    original = dict(status='COMPLETE', revision_id='fixture', revision_content_sha256='fixture-hash', parts=parts)
    write_json(source / 'manifest.json', original)
    monkeypatch.setattr(typed, 'verify_v3_snapshot', lambda path: read_json(path / 'manifest.json'))
    return source


def test_nullable_decimal_mixed_fields_and_leading_zeros(tmp_path, monkeypatch):
    source = source_fixture(tmp_path, monkeypatch)
    out = tmp_path / 'typed'
    manifest = typed.materialize_v3_tables(source, out)
    typed.verify_v3_tables(source, out)
    assert manifest['real_execution_admitted'] is False
    frames = list(typed.iter_v3_tables(source, out, 'PRICE'))
    assert frames[0].stock_code.iloc[0] == '005930'
    assert frames[0].n.iloc[0] == Decimal('1.12345678901234567890')
    assert frames[1].n.iloc[0] == Decimal('2')
    assert pd.isna(frames[0].trade_amount.iloc[0])
    assert frames[1].trade_amount.iloc[0] == 42
    assert frames[0].mixed.iloc[0] == '"abc"'
    assert frames[1].mixed.iloc[0] == '3'
    assert json.loads(frames[1].nested.iloc[0]) == {'y': [1, None]}
    assert pd.isna(frames[0].late.iloc[0])
    assert frames[1].late.iloc[0] == 'value'
    schemas = [pq.read_schema(out / part['file']) for part in manifest['parts']]
    assert all(schema == schemas[0] for schema in schemas)
    assert list(next(typed.iter_v3_tables(source, out, 'PRICE', columns=['stock_code'])).columns) == ['stock_code']


def test_output_hash_rewriting_cannot_forge_source_correspondence(tmp_path, monkeypatch):
    source = source_fixture(tmp_path, monkeypatch)
    out = tmp_path / 'typed'
    manifest = typed.materialize_v3_tables(source, out)
    part = manifest['parts'][0]
    frame = pd.read_parquet(out / part['file'])
    frame.loc[0, 'stock_code'] = '999999'
    frame.to_parquet(out / part['file'], index=False)
    part['sha256'] = digest(out / part['file'])
    write_json(out / 'manifest.json', manifest)
    with pytest.raises(ValueError, match='differ from sealed source'):
        typed.verify_v3_tables(source, out)


def test_no_overwrite_and_failed_source(tmp_path, monkeypatch):
    source = source_fixture(tmp_path, monkeypatch)
    out = tmp_path / 'typed'
    typed.materialize_v3_tables(source, out)
    previous = (out / 'manifest.json').read_bytes()
    with pytest.raises(FileExistsError):
        typed.materialize_v3_tables(source, out)
    assert (out / 'manifest.json').read_bytes() == previous
    def reject(path):
        raise ValueError('Snapshot incomplete')
    monkeypatch.setattr(typed, 'verify_v3_snapshot', reject)
    failed = tmp_path / 'failed'
    with pytest.raises(ValueError, match='incomplete'):
        typed.materialize_v3_tables(source, failed)
    assert read_json(failed / 'manifest.json')['status'] == 'FAILED'


def test_source_manifest_binding_and_path_checks(tmp_path, monkeypatch):
    source = source_fixture(tmp_path, monkeypatch)
    out = tmp_path / 'typed'
    manifest = typed.materialize_v3_tables(source, out)
    manifest['parts'][0]['file'] = '../outside.parquet'
    write_json(out / 'manifest.json', manifest)
    with pytest.raises(ValueError, match='path escaped'):
        list(typed.iter_v3_tables(source, out, 'PRICE'))
    original = read_json(source / 'manifest.json')
    original['revision_id'] = 'changed'
    write_json(source / 'manifest.json', original)
    with pytest.raises(ValueError, match='Source manifest binding'):
        list(typed.iter_v3_tables(source, out, 'PRICE'))


def test_null_then_numeric_and_late_struct_field():
    first = typed._describe([{'a': None}])
    second = typed._describe([{'a': Decimal('0.00001'), 'b': {'v': 2}}])
    merged = {name: typed._merge(first.get(name, {'type': 'null'}), info) for name, info in second.items()}
    table = typed._table([{'a': None}], merged)
    assert table.to_pylist() == [{'a': None, 'b': None}]
