-- quality_checks.sql
-- Each statement should return exactly 1 row.

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

-- 4) Duplicate names count (if name expected unique)
SELECT COUNT(*) AS duplicate_name_groups
FROM (
    SELECT name
    FROM users
    GROUP BY name
    HAVING COUNT(*) > 1
) t;