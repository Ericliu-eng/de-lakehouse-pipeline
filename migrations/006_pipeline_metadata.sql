CREATE TABLE IF NOT EXISTS pipeline_metadata (
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    last_watermark TIMESTAMPTZ,
    last_row_count INT,
    status TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source, symbol)
);