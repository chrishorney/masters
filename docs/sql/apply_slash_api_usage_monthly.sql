-- Slash API monthly usage table (matches Alembic revision g2h3i4j5k6l7)
-- Safe to run once in Supabase SQL Editor (PostgreSQL).

CREATE TABLE IF NOT EXISTS slash_api_usage_monthly (
    id SERIAL NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    by_endpoint JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_slash_api_usage_year_month UNIQUE (year, month),
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_slash_api_usage_monthly_year
    ON slash_api_usage_monthly (year);

CREATE INDEX IF NOT EXISTS ix_slash_api_usage_monthly_month
    ON slash_api_usage_monthly (month);

CREATE INDEX IF NOT EXISTS ix_slash_api_usage_monthly_id
    ON slash_api_usage_monthly (id);

-- Tell Alembic this migration is applied (only if your row was on the previous revision).
-- If you don't use Alembic on this DB, you can skip this block.
UPDATE alembic_version
SET version_num = 'g2h3i4j5k6l7'
WHERE version_num = 'f1a2b3c4d5e6';
