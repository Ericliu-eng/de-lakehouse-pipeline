# Data Model

## Lineage

```text
market_bars
  |-> mart_daily_symbol_summary
  |     `-> mart_symbol_volume_rank
  `-> mart_symbol_latest_price

pipeline_metadata  -> incremental state
load_metadata      -> load audit history
```

All marts are physical PostgreSQL tables refreshed with upsert semantics.

## Model Catalog

| Object | Purpose | Grain | Primary key |
| --- | --- | --- | --- |
| `market_bars` | Normalized Alpha Vantage market bars | One row per timestamp and symbol | `(ts, symbol)` |
| `pipeline_metadata` | Incremental state by source and symbol | One row per source and symbol | `(source, symbol)` |
| `load_metadata` | Load-level audit history | One row per load event | `id` |
| `mart_daily_symbol_summary` | Daily close-price statistics and volume | One row per symbol and trading date | `(symbol, trading_date)` |
| `mart_symbol_latest_price` | Latest price snapshot | One row per symbol | `symbol` |
| `mart_symbol_volume_rank` | Daily symbol ranking by total volume | One row per symbol and trading date | `(symbol, trading_date)` |

## Warehouse Tables

### `market_bars`

- `ts`: timezone-aware market timestamp
- `symbol`: normalized ticker symbol
- `open`, `high`, `low`, `close`: market prices
- `volume`: traded volume
- `source`: upstream source, defaulting to `alpha_vantage`

Quality rules require non-null keys, unique `(ts, symbol)`, non-negative close
price and volume, and data no more than 14 days old.

### `pipeline_metadata`

- `source`, `symbol`: incremental-state key
- `last_watermark`: latest processed market timestamp
- `last_row_count`: rows processed in the latest successful load
- `status`: latest persisted load status
- `updated_at`: state update timestamp

### `load_metadata`

- `id`: load event identifier
- `source`: upstream source
- `load_date`: load date
- `version`: source or run version
- `record_count`: processed record count
- `recorded_at`: audit insert timestamp

## Analytical Marts

| Mart | Columns | Business use |
| --- | --- | --- |
| `mart_daily_symbol_summary` | `symbol`, `trading_date`, `avg_close`, `min_close`, `max_close`, `total_volume`, `created_at` | Compare daily price ranges and volume |
| `mart_symbol_latest_price` | `symbol`, `latest_ts`, `close_price`, `volume`, `updated_at` | Serve the latest symbol snapshot |
| `mart_symbol_volume_rank` | `symbol`, `trading_date`, `total_volume`, `volume_rank` | Find daily volume leaders |

`mart_symbol_volume_rank` uses `DENSE_RANK()` within each trading date.
`created_at` on the daily summary records initial row creation and is not
updated during an upsert.

See `docs/DATA_QUALITY.md` for quality gates and `docs/DEMO_QUERIES.md` for
example analytical queries.
