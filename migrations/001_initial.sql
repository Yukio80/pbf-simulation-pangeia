-- Projeto Pangeia - Event Sourcing Schema
-- Run against PostgreSQL to initialize the event store tables

CREATE TABLE IF NOT EXISTS pangeia_events (
    id BIGSERIAL PRIMARY KEY,
    tick INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pe_tick ON pangeia_events(tick);
CREATE INDEX IF NOT EXISTS idx_pe_type ON pangeia_events(event_type);
CREATE INDEX IF NOT EXISTS idx_pe_agg ON pangeia_events(aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_pe_recorded ON pangeia_events(recorded_at);

-- Snapshots table for fast recovery
CREATE TABLE IF NOT EXISTS pangeia_snapshots (
    id BIGSERIAL PRIMARY KEY,
    tick INTEGER NOT NULL,
    snapshot_type VARCHAR(50) NOT NULL,
    state JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ps_tick ON pangeia_snapshots(tick);
CREATE INDEX IF NOT EXISTS idx_ps_type ON pangeia_snapshots(snapshot_type);
