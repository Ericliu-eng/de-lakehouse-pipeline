## Table: users

### Business Purpose
Stores user-level entities for downstream SQL demos, quality checks, and future joins.

### Grain
1 row per user

### Primary Key
id

### Column Definitions
- id: unique user identifier
- name: user display name
- created_at: initial row creation timestamp
- updated_at: last known update timestamp

### Data Quality Rules
- id must be unique and not null
- name must not be null
- created_at should not be null
- updated_at should not be null after backfill

### Known Limitations
- No foreign keys yet
- No downstream fact tables yet
- Current schema is still user-centric and small-scale