-- Script to rename RAW_ANALYTICS schema to ANALYTICS in Snowflake
-- Run this in Snowflake if you have existing data in RAW_ANALYTICS

USE DATABASE TRAINING_DB;

-- Option 1: Rename existing schema (if RAW_ANALYTICS exists and you want to keep data)
-- ALTER SCHEMA RAW_ANALYTICS RENAME TO ANALYTICS;

-- Option 2: Create new ANALYTICS schema (if it doesn't exist)
CREATE SCHEMA IF NOT EXISTS ANALYTICS;

-- Option 3: If you need to copy data from RAW_ANALYTICS to ANALYTICS
-- First create the analytics schema
-- CREATE SCHEMA IF NOT EXISTS ANALYTICS;

-- Then copy tables (example for one table)
-- CREATE OR REPLACE TABLE ANALYTICS.stock_moving_averages AS 
-- SELECT * FROM RAW_ANALYTICS.stock_moving_averages;

-- CREATE OR REPLACE TABLE ANALYTICS.stock_rsi AS 
-- SELECT * FROM RAW_ANALYTICS.stock_rsi;

-- CREATE OR REPLACE TABLE ANALYTICS.stock_technical_indicators AS 
-- SELECT * FROM RAW_ANALYTICS.stock_technical_indicators;

-- Verify the schema exists
SHOW SCHEMAS LIKE 'ANALYTICS';
