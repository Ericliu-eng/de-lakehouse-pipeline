-- 002_tables.sql
-- Goal: schema evolution (modify existing schema without recreating)

ALTER TABLE users
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Optional: keep updated_at non-null for existing rows (simple backfill)
UPDATE users
SET updated_at = COALESCE(updated_at, created_at, NOW())
WHERE updated_at IS NULL;