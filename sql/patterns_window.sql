-- ========================================
-- Window Function Example
-- Rank stock rows by newest timestamp per symbol
-- ========================================

-- Assign a sequential number (rank) to the data for each stock symbol, ordered by time from newest to oldest.
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