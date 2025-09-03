-- FOSS Data Platform - Cleanup and Retention Policies
-- This file initializes the cleanup system for managing old pipeline operations

-- Create retention policies table
CREATE TABLE IF NOT EXISTS cleanup_policies (
    data_type VARCHAR(50) PRIMARY KEY,
    retention_days INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create cleanup audit log
CREATE TABLE IF NOT EXISTS cleanup_audit (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL,
    cleanup_type VARCHAR(20) NOT NULL, -- 'automatic', 'manual', 'emergency'
    records_deleted INTEGER DEFAULT 0,
    space_freed_bytes BIGINT DEFAULT 0,
    executed_at TIMESTAMP DEFAULT NOW(),
    executed_by VARCHAR(100) DEFAULT 'system'
);

-- Insert default retention policies
INSERT INTO cleanup_policies (data_type, retention_days, description) VALUES
('pipeline_operations', 30, 'Pipeline execution records and progress files'),
('dbt_logs', 7, 'DBT transformation logs and artifacts'),
('failed_operations', 14, 'Failed pipeline operations (kept longer for debugging)'),
('completed_operations', 90, 'Successfully completed operations'),
('system_logs', 30, 'Application and system logs'),
('temp_files', 1, 'Temporary files and cache')
ON CONFLICT (data_type) DO NOTHING;

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for updating timestamps
CREATE TRIGGER update_cleanup_policies_updated_at
    BEFORE UPDATE ON cleanup_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Main cleanup function for pipeline operations
CREATE OR REPLACE FUNCTION cleanup_pipeline_operations(
    p_cleanup_type VARCHAR(20) DEFAULT 'automatic',
    p_executed_by VARCHAR(100) DEFAULT 'system'
) RETURNS TABLE(
    data_type VARCHAR(50),
    records_deleted INTEGER,
    space_freed_bytes BIGINT
) AS $$
DECLARE
    v_retention_days INTEGER;
    v_deleted_count INTEGER := 0;
    v_space_freed BIGINT := 0;
    v_cutoff_date TIMESTAMP;
BEGIN
    -- Get retention policy for pipeline operations
    SELECT retention_days INTO v_retention_days
    FROM cleanup_policies
    WHERE data_type = 'pipeline_operations' AND enabled = true;

    -- If no policy found or disabled, return empty result
    IF v_retention_days IS NULL THEN
        RETURN QUERY SELECT 'pipeline_operations'::VARCHAR(50), 0::INTEGER, 0::BIGINT;
        RETURN;
    END IF;

    -- Calculate cutoff date
    v_cutoff_date := NOW() - INTERVAL '1 day' * v_retention_days;

    -- Note: In a full implementation, this would delete from actual pipeline operations table
    -- For now, we'll just log the cleanup action
    v_deleted_count := 0; -- Placeholder for actual deletion count
    v_space_freed := 0; -- Placeholder for space calculation

    -- Log the cleanup action
    INSERT INTO cleanup_audit (
        data_type,
        cleanup_type,
        records_deleted,
        space_freed_bytes,
        executed_by
    ) VALUES (
        'pipeline_operations',
        p_cleanup_type,
        v_deleted_count,
        v_space_freed,
        p_executed_by
    );

    -- Return results
    RETURN QUERY SELECT
        'pipeline_operations'::VARCHAR(50),
        v_deleted_count,
        v_space_freed;
END;
$$ LANGUAGE plpgsql;

-- Function to get cleanup statistics
CREATE OR REPLACE FUNCTION get_cleanup_stats()
RETURNS TABLE(
    data_type VARCHAR(50),
    retention_days INTEGER,
    enabled BOOLEAN,
    last_cleanup TIMESTAMP,
    total_cleaned INTEGER,
    space_saved BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cp.data_type,
        cp.retention_days,
        cp.enabled,
        MAX(ca.executed_at) as last_cleanup,
        COALESCE(SUM(ca.records_deleted), 0)::INTEGER as total_cleaned,
        COALESCE(SUM(ca.space_freed_bytes), 0)::BIGINT as space_saved
    FROM cleanup_policies cp
    LEFT JOIN cleanup_audit ca ON cp.data_type = ca.data_type
    GROUP BY cp.data_type, cp.retention_days, cp.enabled
    ORDER BY cp.data_type;
END;
$$ LANGUAGE plpgsql;

-- Function to update retention policy
CREATE OR REPLACE FUNCTION update_retention_policy(
    p_data_type VARCHAR(50),
    p_retention_days INTEGER,
    p_enabled BOOLEAN DEFAULT true
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE cleanup_policies
    SET retention_days = p_retention_days,
        enabled = p_enabled,
        updated_at = NOW()
    WHERE data_type = p_data_type;

    IF FOUND THEN
        RETURN true;
    ELSE
        RETURN false;
    END IF;
END;
$$ LANGUAGE plpgsql;
