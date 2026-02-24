INSERT INTO users (name)
SELECT 'Alice'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE name = 'Alice');

INSERT INTO users (name)
SELECT 'Bob'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE name = 'Bob');