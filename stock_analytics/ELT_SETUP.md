# Stock Analytics ELT Setup

## Overview
This project implements an **ELT (Extract, Load, Transform)** pipeline for stock market data analysis using:
- **Airflow** for orchestration
- **Snowflake** for data warehousing
- **dbt** for data transformations

## Architecture

### Data Flow
1. **Extract**: Airflow pulls stock data from yfinance API
2. **Load**: Raw data loaded directly to Snowflake `raw` schema
3. **Transform**: dbt performs transformations in Snowflake to create analytical models

```
yfinance → Airflow → Snowflake (raw) → dbt (staging) → dbt (analytics)
```

## Project Structure

```
stock_analytics/
├── models/
│   ├── input/                    # Input layer
│   │   ├── _sources.yml          # Source definitions
│   │   └── staging/              # Staging models (Views)
│   │       ├── stg_stock_prices.sql
│   │       └── _schema.yml
│   └── output/                   # Output layer
│       └── core/                 # Core models (Tables)
│           ├── stock_moving_averages.sql
│           ├── stock_rsi.sql
│           ├── stock_technical_indicators.sql
│           └── _schema.yml
├── dbt_project.yml
└── profiles.yml

dags/
├── yfinance_to_snowflake_etl.py  # Original ETL DAG
└── stock_elt_with_dbt.py         # New ELT DAG with dbt
```

## Data Models

### Input Layer (Staging)
**Schema**: `staging`
**Materialization**: Views

- `stg_stock_prices`: Cleaned and validated raw stock data with data quality checks

### Output Layer (Core/Analytics)
**Schema**: `analytics`
**Materialization**: Tables

1. **stock_moving_averages**
   - SMA (7, 20, 50, 200 day)
   - EMA (12, 26 day)
   - MACD indicator
   - Volume moving averages

2. **stock_rsi**
   - 14-period Relative Strength Index
   - RSI signals (Overbought/Oversold/Neutral)
   - Price change analysis

3. **stock_technical_indicators**
   - Combined model with all indicators
   - Trend signals (Bullish/Bearish)
   - Volume analysis
   - Complete technical analysis view

## Setup Instructions

### 1. Configure Snowflake Environment Variables

Set these environment variables in your shell or `.env` file:

```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_ROLE="your_role"
export SNOWFLAKE_WAREHOUSE="your_warehouse"
export SNOWFLAKE_DATABASE="your_database"
```

### 2. Configure Airflow Variables

In Airflow UI, set these variables:
- `snowflake_userid`
- `snowflake_password`
- `snowflake_account`
- `snowflake_warehouse`
- `snowflake_database`
- `snowflake_role`
- `snowflake_schema` (should be "raw")
- `yfinance_symbols` (e.g., "AAPL,TSLA,GOOGL")
- `yfinance_time_period` (e.g., "180d")
- `yfinance_interval` (e.g., "1d")

### 3. Test dbt Connection

```bash
cd stock_analytics
dbt debug --profiles-dir .
```

### 4. Run dbt Models Manually (Optional)

```bash
# Install dependencies
dbt deps --profiles-dir .

# Run all models
dbt run --profiles-dir .

# Run specific layers
dbt run --profiles-dir . --select input.staging.*
dbt run --profiles-dir . --select output.core.*

# Test models
dbt test --profiles-dir .
```

### 5. Enable Airflow DAG

The DAG `stock_elt_with_dbt` will:
1. Extract stock data from yfinance
2. Load raw data to Snowflake
3. Run dbt staging models (views)
4. Run dbt core models (tables)
5. Run dbt tests

**Schedule**: Weekdays at 6 PM (after market close)

## Key Differences: ETL vs ELT

| Aspect | ETL (Old) | ELT (New) |
|--------|-----------|-----------|
| Transformation Location | Airflow (Python) | Snowflake (SQL via dbt) |
| Raw Data Storage | Immediately transformed | Stored in raw schema |
| Intermediate Data | None | Staging views |
| Analytics Data | Basic | Advanced (MA, RSI, signals) |
| Scalability | Limited by Airflow | Leverages Snowflake compute |
| Testing | Limited | dbt data tests |
| Documentation | Code comments | dbt docs |

## Running the Pipeline

### Via Airflow UI
1. Navigate to DAGs page
2. Enable `stock_elt_with_dbt` DAG
3. Trigger manually or wait for schedule

### Via Airflow CLI
```bash
airflow dags test stock_elt_with_dbt 2025-11-24
```

## dbt Commands Reference

```bash
# Compile models (check for errors)
dbt compile --profiles-dir .

# Run specific model
dbt run --profiles-dir . --select stock_moving_averages

# Generate documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .

# Run tests only
dbt test --profiles-dir .

# Full refresh (rebuild all tables)
dbt run --profiles-dir . --full-refresh
```

## Technical Indicators Explained

### Moving Averages (SMA)
- **SMA_7**: Short-term trend (1 week)
- **SMA_20**: Medium-term trend (1 month)
- **SMA_50**: Intermediate trend (2.5 months)
- **SMA_200**: Long-term trend (10 months)

### Exponential Moving Averages (EMA)
- **EMA_12**: Fast EMA for MACD
- **EMA_26**: Slow EMA for MACD

### MACD
Moving Average Convergence Divergence = EMA_12 - EMA_26
- Positive: Bullish momentum
- Negative: Bearish momentum

### RSI (Relative Strength Index)
- **> 70**: Overbought (potential sell signal)
- **< 30**: Oversold (potential buy signal)
- **30-70**: Neutral

## Troubleshooting

### dbt Connection Issues
```bash
# Test connection
dbt debug --profiles-dir .

# Check environment variables
echo $SNOWFLAKE_ACCOUNT
```

### Airflow Task Failures
- Check Airflow logs for specific task
- Verify Snowflake connection in Airflow UI
- Ensure dbt project path is correct in DAG

### Schema Not Found
Ensure these schemas exist in Snowflake:
```sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
```

## Next Steps

1. **Add more transformations**:
   - Bollinger Bands
   - Volume-Weighted Average Price (VWAP)
   - Support/Resistance levels

2. **Implement incremental models**:
   - Only process new/changed data

3. **Add data quality tests**:
   - Freshness tests
   - Custom validations

4. **Create aggregate tables**:
   - Daily/Weekly summaries
   - Symbol-level statistics

5. **Connect BI tool**:
   - Tableau/PowerBI to `analytics` schema
   - Dashboard for technical indicators
