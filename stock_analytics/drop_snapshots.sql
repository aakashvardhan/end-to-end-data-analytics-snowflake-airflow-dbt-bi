-- Drop existing snapshot tables to recreate with fixed unique keys
USE DATABASE TRAINING_DB;

DROP TABLE IF EXISTS SNAPSHOTS.stock_prices_snapshot;
DROP TABLE IF EXISTS SNAPSHOTS.rsi_signals_snapshot;

-- Verify
SHOW TABLES IN SCHEMA SNAPSHOTS;
