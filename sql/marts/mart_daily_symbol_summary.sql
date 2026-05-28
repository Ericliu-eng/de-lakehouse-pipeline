-- sql/marts/mart_daily_symbol_summary.sql

-- . 插入/更新数据 (修复后的逻辑)
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