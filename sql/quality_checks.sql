-- quality_checks.sql
-- Each statement should return exactly 1 row.

-- 1) Row count should be > 0
SELECT COUNT(*) AS stock_rows_count
FROM market_bars;

-- 2) Timestamp should not be NULL
SELECT COUNT(*) AS null_ts_count
FROM market_bars
WHERE ts IS NULL;

-- 3) Symbol should not be NULL
SELECT COUNT(*) AS null_symbol_count
FROM market_bars
WHERE symbol IS NULL;

-- 4) Open price should not be NULL
SELECT COUNT(*) AS null_open_count
FROM market_bars
WHERE open IS NULL;

-- 5) High price should not be NULL
SELECT COUNT(*) AS null_high_count
FROM market_bars
WHERE high IS NULL;

-- 6) Low price should not be NULL
SELECT COUNT(*) AS null_low_count
FROM market_bars
WHERE low IS NULL;

-- 7) Close price should not be NULL
SELECT COUNT(*) AS null_close_count
FROM market_bars
WHERE close IS NULL;

-- 8) Volume should not be NULL
SELECT COUNT(*) AS null_volume_count
FROM market_bars
WHERE volume IS NULL;

-- 9) Prices should be non-negative
SELECT COUNT(*) AS negative_price_count
FROM market_bars
WHERE open < 0 OR high < 0 OR low < 0 OR close < 0;

-- 10) Volume should be non-negative
SELECT COUNT(*) AS negative_volume_count
FROM market_bars
WHERE volume < 0;

-- 11) Duplicate business key groups
SELECT COUNT(*) AS duplicate_stock_key_groups
FROM (
    SELECT symbol, ts
    FROM market_bars
    GROUP BY symbol, ts
    HAVING COUNT(*) > 1
) t;