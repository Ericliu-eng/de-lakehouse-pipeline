SELECT *
FROM mart_daily_symbol_summary
ORDER BY trading_date DESC, symbol
LIMIT 10;

SELECT *
FROM mart_symbol_latest_price
ORDER BY latest_ts DESC;

SELECT *
FROM mart_symbol_volume_rank
WHERE trading_date = CURRENT_DATE
ORDER BY volume_rank;