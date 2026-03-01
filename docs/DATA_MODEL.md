# Data Model

## Overview
This repo stores data in Postgres and supports SQL patterns + data quality checks.

---

## Table: users

### Grain
- 1 row per user

### Primary Key
- id

### Columns
- id: unique identifier
- name: user name
- created_at: row creation timestamp (if present)

### Constraints / Rules
- id is NOT NULL and UNIQUE
- name should be NOT NULL
- created_at should be NOT NULL (if present)

### Example Queries Supported
- Count users
- Find newest users
- Detect missing names