"""Materialize sealed v3 JSON into typed, named-column Parquet for local reuse.

Canonical snapshots remain the authority. Decimal JSON numbers are exact Arrow
Decimal256, codes/dates/timestamps remain strings, and nested/mixed-type fields
are JSON text. Neither successful conversion nor verification grants execution.
"""
from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .io import digest, read_json, write_json
from .v3_snapshot import SPECS, verify_v3_snapshot


def _safe(root, filename):
    target = root / filename
    if target.resolve().parent != root.resolve():
        raise ValueError('Materialized path escaped')
    return target


def _rows(path, kind, expected_sha=None):
    if expected_sha is not None and digest(path) != expected_sha:
        raise ValueError('Source part changed')
    values = pq.read_table(path, columns=['pg_json']).column('pg_json').to_pylist()
    rows = [json.loads(value, parse_float=Decimal) for value in values]
    if kind == 'SOURCE_PAYLOAD':
        rows = [dict(zip(['payload_id', 'payload_sha256'], row, strict=True)) for row in rows]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('Expected source object rows')
    return rows


def _json_text(value):
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('Nonfinite JSON numeric')
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + _json_text(v)
                              for k, v in sorted(value.items())) + '}'
    if isinstance(value, list):
        return '[' + ','.join(_json_text(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def _kind(value):
    if value is None:
        return {'type': 'null'}
    if isinstance(value, bool):
        return {'type': 'bool'}
    if isinstance(value, int) and -(2 ** 63) <= value < 2 ** 63:
        return {'type': 'int', 'digits': len(str(abs(value)))}
    if isinstance(value, (Decimal, int)):
        value = Decimal(value)
        if not value.is_finite():
            raise ValueError('Nonfinite source numeric')
        _, digits, exponent = value.as_tuple()
        return {'type': 'decimal', 'scale': max(0, -exponent),
                'digits': max(0, len(digits) + exponent)}
    if isinstance(value, str):
        return {'type': 'string'}
    return {'type': 'json'}


def _merge(left, right):
    if left['type'] == 'null':
        return right.copy()
    if right['type'] == 'null':
        return left.copy()
    kinds = {left['type'], right['type']}
    if kinds <= {'int', 'decimal'}:
        value = dict(type='decimal' if 'decimal' in kinds else 'int',
                     digits=max(left.get('digits', 0), right.get('digits', 0)))
        if value['type'] == 'decimal':
            value['scale'] = max(left.get('scale', 0), right.get('scale', 0))
        return value
    if left['type'] == right['type']:
        return left.copy()
    return {'type': 'json'}


def _describe(rows):
    result = {}
    for row in rows:
        for name, value in row.items():
            result[name] = _merge(result.get(name, {'type': 'null'}), _kind(value))
    return result


def _schema(description):
    fields = []
    simple = {'null': pa.null(), 'bool': pa.bool_(), 'int': pa.int64(),
              'string': pa.string(), 'json': pa.string()}
    for name, info in sorted(description.items()):
        if info['type'] == 'decimal':
            precision = max(1, info['digits'] + info['scale'])
            if precision > 76:
                raise ValueError(f'Numeric precision exceeds Decimal256: {name}')
            dtype = pa.decimal256(precision, info['scale'])
        else:
            dtype = simple[info['type']]
        fields.append(pa.field(name, dtype, nullable=True))
    return pa.schema(fields)


def _table(rows, description):
    schema = _schema(description)
    arrays = []
    for field in schema:
        values = [row.get(field.name) for row in rows]
        kind = description[field.name]['type']
        if kind == 'json':
            values = [None if value is None else _json_text(value) for value in values]
        elif kind == 'decimal':
            values = [None if value is None else Decimal(value) for value in values]
        arrays.append(pa.array(values, type=field.type))
    return pa.Table.from_arrays(arrays, schema=schema)


def _save_checked(table, target):
    pq.write_table(table, target, compression='zstd')
    if not pq.read_table(target).equals(table):
        raise ValueError('Parquet round-trip changed source values')


def materialize_v3_tables(source, out):
    """Verify source once, then derive a new directory; never overwrite output."""
    source, out = Path(source), Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema_version='v3-tables-1', status='MATERIALIZING', real_execution_admitted=False,
                    parts=[], schemas={}, source_manifest_sha256=None,
                    encoding='Decimal256 exact numerics; JSON text for nested/mixed fields; strings preserved')
    write_json(out / 'manifest.json', manifest)
    try:
        source_hash = digest(source / 'manifest.json')
        original = verify_v3_snapshot(source)
        manifest.update(source_manifest_sha256=source_hash,
                        revision_id=original['revision_id'], revision_content_sha256=original['revision_content_sha256'])
        descriptions = {}
        for index, part in enumerate(original['parts']):
            kind = part['member_kind']
            rows = _rows(_safe(source, part['file']), kind, part['sha256'])
            local = _describe(rows)
            combined = descriptions.setdefault(kind, {})
            for name, info in local.items():
                combined[name] = _merge(combined.get(name, {'type': 'null'}), info)
            filename = f'{kind.lower()}-{index:05d}.parquet'
            _save_checked(_table(rows, local), out / filename)
            manifest['parts'].append(dict(file=filename, member_kind=kind, rows=len(rows),
                                          source_file=part['file'], source_sha256=part['sha256'],
                                          local_schema=local))
        # Most parts already have final types; reread canonical JSON only where
        # late nullable/new/mixed fields require schema widening.
        for part in manifest['parts']:
            description = descriptions[part['member_kind']]
            local = part.pop('local_schema')
            encoding_changed = any(local.get(name, {}).get('type') != info['type']
                                   for name, info in description.items())
            if _schema(local) != _schema(description) or encoding_changed:
                rows = _rows(_safe(source, part['source_file']), part['member_kind'], part['source_sha256'])
                _save_checked(_table(rows, description), out / part['file'])
            part['sha256'] = digest(out / part['file'])
        if digest(source / 'manifest.json') != source_hash:
            raise ValueError('Source manifest changed during materialization')
        manifest.update(status='COMPLETE', schemas=descriptions)
        write_json(out / 'manifest.json', manifest)
        return manifest
    except Exception as exc:
        manifest.update(status='FAILED', error=f'{type(exc).__name__}: {exc}')
        write_json(out / 'manifest.json', manifest)
        raise


def _binding(source, out):
    manifest = read_json(out / 'manifest.json')
    if (manifest.get('status') != 'COMPLETE' or manifest.get('schema_version') != 'v3-tables-1'
            or manifest.get('real_execution_admitted') is not False):
        raise ValueError('Materialized tables incomplete or unsupported')
    if digest(source / 'manifest.json') != manifest.get('source_manifest_sha256'):
        raise ValueError('Source manifest binding mismatch')
    original = read_json(source / 'manifest.json')
    if original.get('status') != 'COMPLETE':
        raise ValueError('Source snapshot incomplete')
    for name in ['revision_id', 'revision_content_sha256']:
        if manifest.get(name) != original.get(name):
            raise ValueError('Revision binding mismatch')
    if len(manifest['parts']) != len(original['parts']):
        raise ValueError('Source part count mismatch')
    seen = set()
    for part, source_part in zip(manifest['parts'], original['parts'], strict=True):
        if (part['source_file'] != source_part['file'] or part['source_sha256'] != source_part['sha256']
                or part['member_kind'] != source_part['member_kind'] or part['rows'] != source_part['rows']
                or part['file'] in seen):
            raise ValueError('Source part binding mismatch')
        seen.add(part['file'])
        _safe(out, part['file'])
    return manifest


def verify_v3_tables(source, out):
    """Verify pinned source and reconstruct every typed value independently.

    This full audit detects edited output even when its file hash was updated in
    the derived manifest. Repeated trusted runs may use iter_v3_tables, which
    checks source-manifest binding and per-file hashes without decoding JSON.
    """
    source, out = Path(source), Path(out)
    verify_v3_snapshot(source)
    manifest = _binding(source, out)
    descriptions = {}
    for part in manifest['parts']:
        kind = part['member_kind']
        rows = _rows(_safe(source, part['source_file']), kind, part['source_sha256'])
        actual_schema = _describe(rows)
        combined = descriptions.setdefault(kind, {})
        for name, info in actual_schema.items():
            combined[name] = _merge(combined.get(name, {'type': 'null'}), info)
        target = _safe(out, part['file'])
        if digest(target) != part['sha256']:
            raise ValueError('Materialized file hash mismatch')
        actual = pq.read_table(target)
        expected = _table(rows, manifest['schemas'][kind])
        if not actual.equals(expected):
            raise ValueError(f'Materialized values differ from sealed source: {part["file"]}')
    if descriptions != manifest['schemas']:
        raise ValueError('Materialized schema differs from source schema')
    return manifest


def iter_v3_tables(source, out, kind, *, columns=None):
    """Yield typed Pandas frames with nullable Arrow dtypes; no JSON decoding.

    Run verify_v3_tables once after copying/untrusted changes. Each yielded file
    still gets its checksum checked against the trusted materialization manifest.
    JSON-encoded fields remain strings, with schemas documenting their encoding.
    """
    source, out = Path(source), Path(out)
    manifest = _binding(source, out)
    if kind not in SPECS:
        raise ValueError('Unknown member')
    for part in manifest['parts']:
        if part['member_kind'] != kind:
            continue
        target = _safe(out, part['file'])
        if digest(target) != part['sha256']:
            raise ValueError('Materialized file hash mismatch')
        table = pq.read_table(target, columns=None if columns is None else list(columns))
        if table.num_rows != part['rows']:
            raise ValueError('Materialized row count mismatch')
        yield table.to_pandas(types_mapper=pd.ArrowDtype)
