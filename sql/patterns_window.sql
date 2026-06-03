SELECT
    symbol,
    ts,
    close,
    ROW_NUMBER() OVER (
        PARTITION BY symbol
        ORDER BY ts DESC
    ) AS row_num
FROM market_bars;