-- 1. 创建排名表
CREATE TABLE IF NOT EXISTS mart_symbol_volume_rank (
    symbol TEXT NOT NULL,
    trading_date DATE NOT NULL,
    total_volume BIGINT,
    volume_rank INTEGER,
    -- 复合主键，确保每天每只股票只有一条排名记录
    PRIMARY KEY (symbol, trading_date)
);

-- 2. 执行排名计算并插入
INSERT INTO mart_symbol_volume_rank (symbol, trading_date, total_volume, volume_rank)
SELECT 
    symbol,
    trading_date,
    total_volume,
    -- 使用 DENSE_RANK 确保如果成交量相同，排名会并列且不跳号
    DENSE_RANK() OVER (PARTITION BY trading_date ORDER BY total_volume DESC) as volume_rank
FROM mart_daily_symbol_summary
ON CONFLICT (symbol, trading_date) DO UPDATE SET
    total_volume = EXCLUDED.total_volume,
    volume_rank = EXCLUDED.volume_rank;