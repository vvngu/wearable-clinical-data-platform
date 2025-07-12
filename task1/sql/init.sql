-- TimescaleDB initialization script
-- This script creates the necessary tables and hypertables for storing Fitbit data

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create raw_data table for storing all Fitbit metrics
CREATE TABLE IF NOT EXISTS raw_data (
    timestamp TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable (partitioned by timestamp)
SELECT create_hypertable('raw_data', 'timestamp', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_data_user_id ON raw_data (user_id);
CREATE INDEX IF NOT EXISTS idx_raw_data_metric_type ON raw_data (metric_type);
CREATE INDEX IF NOT EXISTS idx_raw_data_user_metric ON raw_data (user_id, metric_type);
CREATE INDEX IF NOT EXISTS idx_raw_data_timestamp ON raw_data (timestamp DESC);

-- Create continuous aggregates for different time intervals
-- 1-minute aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', timestamp) AS bucket,
    user_id,
    metric_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS count,
    STDDEV(value) AS stddev_value
FROM raw_data
GROUP BY bucket, user_id, metric_type;

-- 1-hour aggregates  
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1h
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS bucket,
    user_id,
    metric_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS count,
    STDDEV(value) AS stddev_value
FROM raw_data
GROUP BY bucket, user_id, metric_type;

-- 1-day aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS data_1d
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS bucket,
    user_id,
    metric_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS count,
    STDDEV(value) AS stddev_value
FROM raw_data
GROUP BY bucket, user_id, metric_type;

-- Create policies for continuous aggregates refresh
SELECT add_continuous_aggregate_policy('data_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

SELECT add_continuous_aggregate_policy('data_1h',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

SELECT add_continuous_aggregate_policy('data_1d',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

-- Create table for tracking ingestion metadata
CREATE TABLE IF NOT EXISTS ingestion_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    last_ingestion_time TIMESTAMPTZ NOT NULL,
    records_processed INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    ingestion_duration_seconds DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create table for user management
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255),
    fitbit_user_id VARCHAR(50),
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create data retention policies (optional - adjust based on your needs)
-- Keep raw data for 1 year
SELECT add_retention_policy('raw_data', INTERVAL '365 days');

-- Function to get appropriate table based on time range
CREATE OR REPLACE FUNCTION get_optimal_table(
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ
) RETURNS TEXT AS $$
DECLARE
    time_diff INTERVAL;
    table_name TEXT;
BEGIN
    time_diff := end_date - start_date;
    
    -- If query spans more than 7 days, use daily aggregates
    IF time_diff > INTERVAL '7 days' THEN
        table_name := 'data_1d';
    -- If query spans more than 6 hours, use hourly aggregates
    ELSIF time_diff > INTERVAL '6 hours' THEN
        table_name := 'data_1h';
    -- If query spans more than 1 hour, use minute aggregates
    ELSIF time_diff > INTERVAL '1 hour' THEN
        table_name := 'data_1m';
    -- For short queries, use raw data
    ELSE
        table_name := 'raw_data';
    END IF;
    
    RETURN table_name;
END;
$$ LANGUAGE plpgsql;

-- Create indexes on continuous aggregates
CREATE INDEX IF NOT EXISTS idx_data_1m_bucket ON data_1m (bucket DESC);
CREATE INDEX IF NOT EXISTS idx_data_1m_user_metric ON data_1m (user_id, metric_type);

CREATE INDEX IF NOT EXISTS idx_data_1h_bucket ON data_1h (bucket DESC);
CREATE INDEX IF NOT EXISTS idx_data_1h_user_metric ON data_1h (user_id, metric_type);

CREATE INDEX IF NOT EXISTS idx_data_1d_bucket ON data_1d (bucket DESC);
CREATE INDEX IF NOT EXISTS idx_data_1d_user_metric ON data_1d (user_id, metric_type);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fitbit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fitbit_user;
