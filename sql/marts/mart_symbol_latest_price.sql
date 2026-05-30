-- Build latest price snapshot per symbol.
WITH ranked_bars AS (
    SELECT
        symbol,
        ts AS latest_ts,
        close AS close_price,
        volume,
        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY ts DESC
        ) AS rn
    FROM market_bars
)
INSERT INTO mart_symbol_latest_price (
    symbol,
    latest_ts,
    close_price,
    volume
)
SELECT
    symbol,
    latest_ts,
    close_price,
    volume
FROM ranked_bars
WHERE rn = 1
ON CONFLICT (symbol) DO UPDATE SET
    latest_ts = EXCLUDED.latest_ts,
    close_price = EXCLUDED.close_price,
    volume = EXCLUDED.volume,
    updated_at = CURRENT_TIMESTAMP;
