-- Build daily symbol-level close-price summary and volume totals.
INSERT INTO mart_daily_symbol_summary (
    symbol,
    trading_date,
    avg_close,
    min_close,
    max_close,
    total_volume
)
SELECT
    symbol,
    ts::DATE AS trading_date,
    AVG(close) AS avg_close,
    MIN(close) AS min_close,
    MAX(close) AS max_close,
    SUM(volume) AS total_volume
FROM market_bars
GROUP BY symbol, ts::DATE
ON CONFLICT (symbol, trading_date) DO UPDATE SET
    avg_close = EXCLUDED.avg_close,
    min_close = EXCLUDED.min_close,
    max_close = EXCLUDED.max_close,
    total_volume = EXCLUDED.total_volume;
