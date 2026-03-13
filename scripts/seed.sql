INSERT INTO market_bars (
    ts, symbol, open, high, low, close, volume
)
VALUES (
    '2026-01-01 00:00:00+00',
    'TEST',
    100, 110, 90, 105, 1000
)
ON CONFLICT (ts, symbol) DO NOTHING;