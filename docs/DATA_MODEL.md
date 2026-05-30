# Data Model

## Table: market_bars

### Business Purpose
Stores normalized stock market bars parsed from Alpha Vantage raw payloads.

### Grain
One row per `(ts, symbol)`.

### Primary Key
`(ts, symbol)`

### Columns
- `ts`: timezone-aware market timestamp
- `symbol`: stock ticker symbol
- `open`: opening price
- `high`: high price
- `low`: low price
- `close`: closing price
- `volume`: traded volume

### Quality Rules
- `ts` must not be null
- `symbol` must not be null
- `(ts, symbol)` must be unique
- `close >= 0`
- `volume >= 0`

## Table: pipeline_metadata

### Business Purpose
Tracks incremental processing state for each source and symbol.

### Grain
One row per `(source, symbol)`.

### Primary Key
`(source, symbol)`

### Columns
- `source`: upstream source name
- `symbol`: stock ticker symbol
- `last_watermark`: latest processed timestamp
- `last_row_count`: number of rows processed in the last successful load
- `status`: latest pipeline status
- `updated_at`: metadata update timestamp

## Table: load_metadata

### Business Purpose
Records load-level metadata for observability and auditability.

### Grain
One row per load event.

### Columns
- `id`: load metadata identifier
- `source`: upstream source name
- `load_date`: date of the load
- `version`: source or run version
- `record_count`: number of records loaded
- `recorded_at`: metadata insert timestamp

## Mart: mart_daily_symbol_summary

### Business Question
What are each symbol's daily close-price summary statistics and total volume?

### Grain
One row per `(symbol, trading_date)`.

### Primary Key
`(symbol, trading_date)`

### Columns
- `symbol`
- `trading_date`
- `avg_close`
- `min_close`
- `max_close`
- `total_volume`
- `created_at`

## Mart: mart_symbol_latest_price

### Business Question
What is the latest close price and volume for each symbol?

### Grain
One row per `symbol`.

### Primary Key
`symbol`

### Columns
- `symbol`
- `latest_ts`
- `close_price`
- `volume`
- `updated_at`

## Mart: mart_symbol_volume_rank

### Business Question
Which symbols had the highest total trading volume on each trading date?

### Grain
One row per `(symbol, trading_date)`.

### Primary Key
`(symbol, trading_date)`

### Columns
- `symbol`
- `trading_date`
- `total_volume`
- `volume_rank`
