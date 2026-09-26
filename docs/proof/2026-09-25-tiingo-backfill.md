# Tiingo History Backfill — 2026-09-25

Live run of the Tiingo history backfill against the local development
warehouse (PostgreSQL 16, Docker) on Windows 11. The API token was read from
`.env` and is not recorded here.

## Before

```text
source         rows
alpha_vantage  1,225
```

## Command

```bash
python -m de_lakehouse_pipeline.cli tiingo_backfill --symbol AAPL,AMZN,GOOGL,JNJ,JPM,META,MSFT,NVDA,WMT,XOM
```

Wall time: 20.5 s for 10 requests.

```text
AAPL: fetched 11537 bar(s) (1980-12-12 to 2026-09-25), inserted 11359, kept 178 existing; 178 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
AMZN: fetched 7387 bar(s) (1997-05-15 to 2026-09-25), inserted 7287, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
GOOGL: fetched 5561 bar(s) (2004-08-19 to 2026-09-25), inserted 5396, kept 165 existing; 165 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
JNJ: fetched 14303 bar(s) (1970-01-02 to 2026-09-25), inserted 14203, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
JPM: fetched 10768 bar(s) (1983-12-30 to 2026-09-25), inserted 10668, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
META: fetched 3609 bar(s) (2012-05-18 to 2026-09-25), inserted 3509, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
MSFT: fetched 10213 bar(s) (1986-03-13 to 2026-09-25), inserted 10037, kept 176 existing; 176 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
NVDA: fetched 6962 bar(s) (1999-01-22 to 2026-09-25), inserted 6862, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
WMT: fetched 13633 bar(s) (1972-08-25 to 2026-09-25), inserted 13533, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
XOM: fetched 14303 bar(s) (1970-01-02 to 2026-09-25), inserted 14203, kept 100 existing; 100 overlapping day(s), 0 beyond 0.5% close difference (max 0.0%)
```

## After

```text
source         rows
alpha_vantage   1,225   (unchanged)
tiingo         97,057
total          98,282
```

- Fetched 98,276 bars; inserted 97,057; kept 1,219 existing Alpha Vantage rows.
- 1,219 overlapping days: 0 closes differ by more than 0.5% (max 0.0%).
- Quality checks for AAPL: 6/6 passed (not-null, unique `(symbol, ts)`,
  non-negative close and volume, freshness for `alpha_vantage`).
- `make run-marts` rebuilt the marts in 1.7 s: `mart_daily_symbol_summary`
  98,280 rows, `mart_symbol_volume_rank` 98,280, `mart_symbol_latest_price` 13.
  The two-row gap comes from pre-existing intraday test rows (`TESTA`, `TESTB`)
  that share a trading date.

## Notes

- Prices are unadjusted in both sources, so splits appear as jumps
  (AAPL closed at 499.23 on 2020-08-28 and 129.04 on 2020-08-31).
- Rerunning the command inserts 0 rows; this is covered by
  `tests/integration/test_tiingo_backfill.py`.
