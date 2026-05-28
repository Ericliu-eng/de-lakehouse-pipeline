-- This file is for SQL pattern reference only.
-- It is not part of the migration pipeline.
-- Do not run this file in CI unless intentionally testing window functions.
SELECT
    ts,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    ROW_NUMBER() OVER (
        PARTITION BY symbol
        ORDER BY ts DESC
    ) AS row_num
FROM market_bars;