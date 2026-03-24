-- sql/marts/mart_daily_symbol_summary.sql

-- 1. 创建表逻辑保持不变
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

-- 2. 插入/更新数据 (修复后的逻辑)
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
    ts::DATE as trading_date,  -- 关键点：强制转换为 DATE
    AVG(close) as avg_close,
    MIN(close) as min_close,
    MAX(close) as max_close,
    SUM(volume) as total_volume
FROM market_bars 
GROUP BY symbol, ts::DATE      -- 关键点：按照日期聚合，而不是精确时间戳
ON CONFLICT (symbol, trading_date) DO UPDATE SET
    avg_close = EXCLUDED.avg_close,
    min_close = EXCLUDED.min_close,
    max_close = EXCLUDED.max_close,
    total_volume = EXCLUDED.total_volume;