-- Rank symbols by daily total volume.
INSERT INTO mart_symbol_volume_rank (
    symbol,
    trading_date,
    total_volume,
    volume_rank
)
SELECT
    symbol,
    trading_date,
    total_volume,
    DENSE_RANK() OVER (
        PARTITION BY trading_date
        ORDER BY total_volume DESC
    ) AS volume_rank
FROM mart_daily_symbol_summary
ON CONFLICT (symbol, trading_date) DO UPDATE SET
    total_volume = EXCLUDED.total_volume,
    volume_rank = EXCLUDED.volume_rank;
