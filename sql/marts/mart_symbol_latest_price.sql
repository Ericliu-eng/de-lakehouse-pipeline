-- 1. 创建快照表
CREATE TABLE IF NOT EXISTS mart_symbol_latest_price (
    symbol TEXT PRIMARY KEY,              -- 每个股票只有一行最新数据
    latest_ts TIMESTAMPTZ,                -- 和源表 ts 保持一致
    close_price NUMERIC(16, 4),
    volume BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 提取每个 symbol 最新一条并 upsert
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