# OHLCV20 test fixtures

These small snapshots make the OHLCV20 contract tests run in a clean checkout. They are test inputs, not approval to execute a real backtest.

- `rights-price-payment-inputs-v4.parquet` is a byte-for-byte copy of `ted-startup/data/sources/ohlcv-admission-20260922/settlement-contract-v4/rights-price-payment-inputs.parquet` (SHA-256 `c96aa8911fb4bb46d8d198596d6b1914120d587edcd6c7b2f9fb0fa1a7d7d2d5`, 12,790 bytes). Its rows have `execution_admitted=false`.
- `confirmed-strategy-policy-v1.json` is a copy of `ted-startup/docs/research/evidence/ohlcv-admission-2026-09-22/confirmed-strategy-policy-v1.json` (SHA-256 `3905d28a3bb5d4a91030d0d08decf9db0840d2b40a94a39712953a9f0878ef54`). Set `OHLCV20_POLICY_DELIVERY` to the current delivered JSON path to check both copies in one test run.

Update these snapshots only after reviewing the source changes and their hashes. The tests validate code behavior and policy parity; they do not establish source admission.
