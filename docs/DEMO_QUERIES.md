# Demo Queries

## Question 1: Which symbols had the highest trading volume by day?

Use `mart_symbol_volume_rank` to inspect daily volume leaders.

```sql
SELECT
    trading_date,
    symbol,
    total_volume,
    volume_rank
FROM mart_symbol_volume_rank
ORDER BY trading_date DESC, volume_rank ASC
LIMIT 20;
```

## Question 2: What is the latest close price for each symbol?

Use `mart_symbol_latest_price` as the current-symbol snapshot table.

```sql
SELECT
    symbol,
    latest_ts,
    close_price,
    volume,
    updated_at
FROM mart_symbol_latest_price
ORDER BY latest_ts DESC, symbol;
```

## Question 3: What is each symbol's daily close-price range and total volume?

Use `mart_daily_symbol_summary` to compare daily summary statistics.

```sql
SELECT
    trading_date,
    symbol,
    avg_close,
    min_close,
    max_close,
    max_close - min_close AS close_range,
    total_volume
FROM mart_daily_symbol_summary
ORDER BY trading_date DESC, symbol
LIMIT 20;
```

## Raw Table Sanity Check

```sql
SELECT
    symbol,
    COUNT(*) AS row_count,
    MIN(ts) AS first_ts,
    MAX(ts) AS latest_ts
FROM market_bars
GROUP BY symbol
ORDER BY symbol;
```
