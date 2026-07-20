-- PostgreSQL Initial Setup Script for SellIA Production Database
-- Runs automatically via docker-compose init volume

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sales_cycles_user_id ON sales_cycles(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_cycles_status ON sales_cycles(status);
CREATE INDEX IF NOT EXISTS idx_sales_cycles_created_at ON sales_cycles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_automations_enabled ON automations(enabled);
CREATE INDEX IF NOT EXISTS idx_automations_user_id ON automations(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET pg_stat_statements.max = 10000;

-- Set connection limits
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '2GB';
ALTER SYSTEM SET ssl = 'on';

-- Create audit logging function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        id, user_id, action, entity_type, entity_id, changes, ip_address, created_at
    ) VALUES (
        gen_random_uuid(),
        current_setting('app.current_user_id')::varchar,
        TG_ARGV[0],
        TG_TABLE_NAME,
        NEW.id::varchar,
        jsonb_build_object('old', row_to_json(OLD), 'new', row_to_json(NEW)),
        current_setting('app.client_ip', true),
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enable query logging for slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = true;
ALTER SYSTEM SET log_lock_waits = true;

-- Set replication settings (if using streaming replication)
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET hot_standby = 'on';

-- Reload configuration
SELECT pg_reload_conf();

-- Display current settings
SELECT name, setting FROM pg_settings
WHERE name IN (
    'max_connections',
    'shared_buffers',
    'effective_cache_size',
    'wal_level',
    'max_wal_senders',
    'ssl'
)
ORDER BY name;
