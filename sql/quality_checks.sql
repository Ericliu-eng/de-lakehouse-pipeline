-- ========================================
-- Data Quality Checks (starter)
-- ========================================

-- 1) Row count should be > 0
SELECT COUNT(*) AS users_count
FROM users;

-- 2) Primary key should not be NULL
SELECT COUNT(*) AS null_id_count
FROM users
WHERE id IS NULL;

-- 3) Name should not be NULL (business rule)
SELECT COUNT(*) AS null_name_count
FROM users
WHERE name IS NULL;

-- 4) Detect duplicate names (if name is expected unique for now)
SELECT
    name,
    COUNT(*) AS cnt
FROM users
GROUP BY name
HAVING COUNT(*) > 1;