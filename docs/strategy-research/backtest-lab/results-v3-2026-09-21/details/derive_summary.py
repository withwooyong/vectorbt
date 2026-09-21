"""Derive matched descriptive report figures from the verified completed batch."""
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

import numpy as np
import pandas as pd

repo = Path('C:/Users/aeby/vscode/stock/vectorbt')
sys.path.insert(0, str(repo))
from research.krx_lab.io import read_json, write_json, digest
from research.krx_lab.v3_report import _full_validation, _PAIRS

batch = repo.parent / 'vectorbt-data/krx-v3-20260921-combined'
prepared = repo.parent / 'vectorbt-data/krx-v3-20260921-prepared-r2'
out = repo / 'docs/strategy-research/backtest-lab/results-v3-2026-09-21/details'
assert read_json(batch / 'merge-manifest.json')['status'] == 'COMPLETE'
summary = read_json(batch / 'summary.json')
assert summary['status'] == 'COMPLETE' and summary['attempted_runs'] == 2464
rows = summary['results']
complete = {(r['family'], r['entry_id'], r['exit_id']): r for r in _full_validation(rows)}
paired = []
for (family, entry, basic_exit), basic in complete.items():
    if family != 'basic':
        continue
    wide_exit = _PAIRS[basic_exit]
    wide = complete.get(('wide', entry, wide_exit))
    if wide is None:
        continue
    record = {'entry_id': entry, 'basic_exit': basic_exit, 'wide_exit': wide_exit,
              'basic_return': basic['avg_return'], 'wide_return': wide['avg_return'],
              'difference_pp': 100 * (wide['avg_return'] - basic['avg_return']),
              'basic_worst_mdd': basic['worst_mdd'], 'wide_worst_mdd': wide['worst_mdd']}
    for group, exit_id in [('basic', basic_exit), ('wide', wide_exit)]:
        selected = [r for r in rows if r['family'] == group and r['entry_id'] == entry
                    and r['exit_id'] == exit_id and r['phase'] == 'validation'
                    and r['cost_model'] == 'DATED_V3_RULES' and r['delay'] == 1]
        assert len(selected) == 4 and {r['year'] for r in selected} == {2020, 2021, 2022, 2023}
        assert all(r['status'] == 'SUCCEEDED' and r['ledger_check']['status'] == 'PASS' for r in selected)
        record[group + '_exposure'] = float(np.mean([r['metrics']['average_exposure_fraction'] for r in selected]))
        days, trades = 0, 0
        for r in selected:
            frame = pd.read_parquet(batch / 'runs' / r['run_id'] / 'trades.parquet')
            duration = (pd.to_datetime(frame.exit_date) - pd.to_datetime(frame.entry_date)).dt.days
            days += int(duration.sum())
            trades += len(frame)
        record[group + '_holding_days_sum'] = days
        record[group + '_trade_count'] = trades
        record[group + '_holding_days'] = days / trades if trades else None
    paired.append(record)

groups = []
for basic_exit, wide_exit in _PAIRS.items():
    selected = [r for r in paired if r['basic_exit'] == basic_exit]
    group = {'basic_exit': basic_exit, 'wide_exit': wide_exit, 'pair_count': len(selected)}
    for name in ['basic_return', 'wide_return', 'difference_pp', 'basic_worst_mdd', 'wide_worst_mdd',
                 'basic_exposure', 'wide_exposure']:
        group[name] = float(np.mean([r[name] for r in selected])) if selected else None
    for family in ['basic', 'wide']:
        count = sum(r[family + '_trade_count'] for r in selected)
        group[family + '_trade_count'] = count
        group[family + '_holding_days'] = (sum(r[family + '_holding_days_sum'] for r in selected) / count
                                           if count else None)
    groups.append(group)

blocked = Counter()
observations = defaultdict(Counter)
observation_reasons = defaultdict(set)
observation_runs = defaultdict(set)
for row in rows:
    if row['status'] != 'BLOCKED':
        continue
    for reason in row['issues']:
        kind, day, identity = reason.split(':', 2)
        blocked[kind] += 1
        observations[(day, identity)][row['family']] += 1
        observation_reasons[(day, identity)].add(kind)
        observation_runs[(day, identity)].add(row['run_id'])
price = pd.read_parquet(prepared / 'prices.parquet', columns=[
    'date', 'instrument_id', 'display_code', 'market', 'open', 'high', 'low', 'close', 'volume', 'status', 'eligible'])
price['instrument_id'] = price.instrument_id.astype(str)
price = price.loc[price.instrument_id.isin({identity for _, identity in observations})]
lookup = price.set_index(['date', 'instrument_id'])
details = []
for (day, identity), counts in sorted(observations.items()):
    raw = lookup.loc[(pd.Timestamp(day), identity)].to_dict()
    previous = price.loc[(price.instrument_id == identity) & (price.date < pd.Timestamp(day))].sort_values('date')
    details.append({'date': day, 'instrument_id': identity, **raw,
                    'previous_market': previous.iloc[-1].market if len(previous) else None,
                    'reasons': sorted(observation_reasons[(day, identity)]),
                    'distinct_blocked_runs': len(observation_runs[(day, identity)]),
                    'issue_counts_by_family': dict(counts), 'issue_occurrences': sum(counts.values())})

result = {
    'source_summary_sha256': digest(batch / 'summary.json'),
    'analysis_code_sha256': digest(__file__),
    'pair_count': len(paired), 'possible_pairs': 56,
    'wide_higher': sum(r['difference_pp'] > 1e-10 for r in paired),
    'basic_higher': sum(r['difference_pp'] < -1e-10 for r in paired),
    'ties': sum(abs(r['difference_pp']) <= 1e-10 for r in paired),
    'wide_worse_worst_mdd': sum(r['wide_worst_mdd'] > r['basic_worst_mdd'] + 1e-12 for r in paired),
    'mean_difference_pp': float(np.mean([r['difference_pp'] for r in paired])) if paired else None,
    'groups': groups, 'pairs': paired,
    'no_trade_successes': sum(r['status'] == 'SUCCEEDED' and r['metrics']['trade_count'] == 0 for r in rows),
    'blocked_reasons': dict(blocked), 'blocked_observation_count': len(details),
    'blocked_instrument_count': len({r['instrument_id'] for r in details}),
}
write_json(out / 'comparison-summary.json', result)
write_json(out / 'blocked-observations.json', details)
print(json.dumps({k: v for k, v in result.items() if k != 'pairs'}, ensure_ascii=False, indent=2))
