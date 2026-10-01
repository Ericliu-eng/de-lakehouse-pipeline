from pathlib import Path


def test_observability_migration_defines_expected_tables_and_cascades() -> None:
    root = Path(__file__).resolve().parents[2]
    sql = (root / "migrations" / "009_observability.sql").read_text(encoding="utf-8")

    for table_name in (
        "pipeline_runs",
        "pipeline_run_steps",
        "quality_check_results",
        "incident_analyses",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql

    assert sql.count("REFERENCES pipeline_runs(id) ON DELETE CASCADE") == 3
    assert "external_run_id UUID NOT NULL UNIQUE" in sql
    assert "likely_causes JSONB" in sql
    assert "recommended_steps JSONB" in sql
