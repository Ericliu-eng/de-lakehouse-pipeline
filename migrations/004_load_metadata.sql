CREATE TABLE IF NOT EXISTS load_metadata (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    load_date DATE NOT NULL,
    version TEXT,
    record_count INT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);