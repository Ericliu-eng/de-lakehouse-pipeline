
-- Create mart tables up front so fresh databases (and CI) never hit "table does not exist"
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
    symbol TEXT PRIMARY KEY,              -- one row per symbol: its latest bar
    latest_ts TIMESTAMPTZ,                -- same type as the source ts column
    close_price NUMERIC(16, 4),
    volume BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily volume ranking
CREATE TABLE IF NOT EXISTS mart_symbol_volume_rank (
    symbol TEXT NOT NULL,
    trading_date DATE NOT NULL,
    total_volume BIGINT,
    volume_rank INTEGER,
    -- one rank row per symbol per trading day
    PRIMARY KEY (symbol, trading_date)
);
