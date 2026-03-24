
--在这里先跑 防止ci 不通过  说table not exist
CREATE TABLE IF NOT EXISTS mart_daily_symbol_summary (
    symbol VARCHAR(10),
    trading_date DATE,
    avg_close DECIMAL(16, 4),
    min_close DECIMAL(16, 4),
    max_close DECIMAL(16, 4),
    total_volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, trading_date)
);

CREATE TABLE IF NOT EXISTS mart_symbol_latest_price (
    symbol TEXT PRIMARY KEY,              -- 每个股票只有一行最新数据
    latest_ts TIMESTAMPTZ,                -- 和源表 ts 保持一致
    close_price NUMERIC(16, 4),
    volume BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mart_symbol_volume_rank (
    symbol TEXT NOT NULL,
    trading_date DATE NOT NULL,
    total_volume BIGINT,
    volume_rank INTEGER,
    -- 复合主键，确保每天每只股票只有一条排名记录
    PRIMARY KEY (symbol, trading_date)
);
