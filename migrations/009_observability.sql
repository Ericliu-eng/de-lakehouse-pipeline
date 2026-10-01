CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    external_run_id UUID NOT NULL UNIQUE,
    source TEXT,
    symbol TEXT,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    quality_status TEXT NOT NULL DEFAULT 'NOT_EVALUATED'
        CHECK (quality_status IN ('NOT_EVALUATED', 'PASS', 'WARN', 'FAIL')),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_ms BIGINT CHECK (duration_ms IS NULL OR duration_ms >= 0),
    rows_processed INT NOT NULL DEFAULT 0 CHECK (rows_processed >= 0),
    error_type TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_pipeline_runs_recent
    ON pipeline_runs (started_at DESC);

CREATE INDEX IF NOT EXISTS ix_pipeline_runs_pipeline_status
    ON pipeline_runs (pipeline_name, status, started_at DESC);

CREATE TABLE IF NOT EXISTS pipeline_run_steps (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_ms BIGINT CHECK (duration_ms IS NULL OR duration_ms >= 0),
    row_count INT CHECK (row_count IS NULL OR row_count >= 0),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_pipeline_run_steps_run
    ON pipeline_run_steps (run_id, id);

CREATE TABLE IF NOT EXISTS quality_check_results (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS', 'WARN', 'FAIL')),
    metric_value DOUBLE PRECISION,
    threshold DOUBLE PRECISION,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_quality_check_results_run
    ON quality_check_results (run_id, id);

CREATE TABLE IF NOT EXISTS incident_analyses (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    summary TEXT NOT NULL,
    likely_causes JSONB NOT NULL DEFAULT '[]'::JSONB,
    recommended_steps JSONB NOT NULL DEFAULT '[]'::JSONB,
    analysis_method TEXT NOT NULL DEFAULT 'rule_based',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_incident_analyses_run
    ON incident_analyses (run_id, created_at DESC);
