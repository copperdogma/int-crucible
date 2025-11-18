-- Kosmos PostgreSQL Initialization Script
-- This script runs automatically when PostgreSQL container starts for the first time
-- Location: /docker-entrypoint-initdb.d/init.sql

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";        -- UUID generation functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- Trigram matching for text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";        -- GIN indexes for better performance
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Track query statistics

-- Configure PostgreSQL for optimal performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET pg_stat_statements.max = 10000;

-- Connection and memory settings (optimized for Docker)
ALTER SYSTEM SET max_connections = 100;
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
ALTER SYSTEM SET max_wal_size = '4GB';

-- Query optimization settings
ALTER SYSTEM SET enable_partitionwise_join = on;
ALTER SYSTEM SET enable_partitionwise_aggregate = on;

-- Logging configuration for performance monitoring
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries taking >1s
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_duration = off;
ALTER SYSTEM SET log_lock_waits = on;

-- Autovacuum settings for maintaining performance
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '1min';

-- Create database schema comment
COMMENT ON DATABASE kosmos IS 'Kosmos AI Scientist - Main application database';

-- Note: Table creation will be handled by Alembic migrations
-- This script only sets up extensions and optimal configuration
