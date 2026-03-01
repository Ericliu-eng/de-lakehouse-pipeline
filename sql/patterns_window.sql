-- ========================================
-- Window Function Example
-- Rank users by newest created_at
-- ========================================

SELECT
    id,
    name,
    created_at,
    ROW_NUMBER() OVER (ORDER BY created_at DESC) AS row_num
FROM users;


-- ========================================
-- Deduplication Example
-- Keep latest record per user name
-- ========================================

SELECT *
FROM (
    SELECT
        id,
        name,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY name
            ORDER BY created_at DESC
        ) AS rn
    FROM users
) t
WHERE rn = 1;