# Schema Evolution

## Rules

Database schema changes are applied through numbered SQL files in
`migrations/`. Never edit an already-applied migration to change deployed
state. Add a new migration, make it safe to run in the expected environment,
and update tests and documentation in the same pull request.

For each schema change:

1. Add the next numbered migration.
2. Update writers before making new fields mandatory, or use a compatible
   default/backfill sequence.
3. Update readers, marts, serving code, and the data contract as applicable.
4. Test both a fresh database and an upgrade from the prior schema.
5. Run database smoke and integration tests.
6. Record breaking behavior and rollback/recovery notes in the pull request.

## Current Migration History

| Migration | Purpose |
| --- | --- |
| `001_init.sql` | Initial database objects |
| `002_tables.sql` | Early table evolution |
| `003_market_bars.sql` | Market-bar fact table and `(ts, symbol)` primary key |
| `004_load_metadata.sql` | Load audit history |
| `005_marts.sql` | Analytical mart tables |
| `006_pipeline_metadata.sql` | Per-source/per-symbol watermark state |
| `007_drop_legacy_users.sql` | Remove the legacy example table |
| `008_add_source_to_market_bars.sql` | Add required source with an Alpha Vantage default |

## Safe Change Patterns

For a new required column, prefer expand/backfill/contract:

1. add it as nullable or with a safe default;
2. deploy writers and backfill existing rows;
3. verify completeness;
4. enforce `NOT NULL` in a later migration.

For destructive changes, create a replacement object or backup/export before
dropping data. Document the recovery command and expected downtime. The
repository does not currently provide automated down migrations.
