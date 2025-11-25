# Quick Start Guide - Stock Analytics ELT Pipeline

## What Was Created

### ✅ dbt Models Structure
```
models/
├── input/
│   ├── _sources.yml                          # Defines raw data sources
│   └── staging/
│       ├── stg_stock_prices.sql              # Staging view (cleaned data)
│       └── _schema.yml                        # Documentation
└── output/
    └── core/
        ├── stock_moving_averages.sql          # SMA/EMA/MACD (table)
        ├── stock_rsi.sql                      # RSI indicator (table)
        ├── stock_technical_indicators.sql     # Combined indicators (table)
        └── _schema.yml                        # Documentation
```

### ✅ Airflow DAG
- **File**: `../dags/stock_elt_with_dbt.py`
- **Purpose**: Extract → Load → Transform (with dbt)
- **Schedule**: Weekdays at 6 PM

### ✅ Configuration Files
- `dbt_project.yml` - Updated with input/output configs
- `profiles.yml` - Snowflake connection settings
- `verify_setup.sh` - Setup verification script

## Step-by-Step Execution

### Step 1: Set Environment Variables
```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_ROLE="your_role"
export SNOWFLAKE_WAREHOUSE="your_warehouse"
export SNOWFLAKE_DATABASE="your_database"
```

### Step 2: Verify Setup
```bash
cd /Users/aakashvardhan/Documents/end-to-end-data-analytics-snowflake-airflow-dbt-bi/stock_analytics
./verify_setup.sh
```

### Step 3: Test dbt Locally
```bash
# Test connection
dbt debug --profiles-dir .

# Compile models (check for errors)
dbt compile --profiles-dir .

# Run staging models only
dbt run --profiles-dir . --select input.staging.*

# Run all core models
dbt run --profiles-dir . --select output.core.*

# Run all models
dbt run --profiles-dir .

# Run tests
dbt test --profiles-dir .
```

### Step 4: Deploy to Airflow
```bash
# Copy DAG file (if not already in dags folder)
cp ../dags/stock_elt_with_dbt.py $AIRFLOW_HOME/dags/

# Test the DAG
airflow dags test stock_elt_with_dbt 2025-11-24

# Enable in UI or via CLI
airflow dags unpause stock_elt_with_dbt
```

## Data Flow Diagram

```
┌─────────────┐
│  yfinance   │
│     API     │
└──────┬──────┘
       │ Extract (Airflow)
       ▼
┌─────────────┐
│  Snowflake  │
│ raw schema  │ ← Raw data loaded here
└──────┬──────┘
       │ Transform (dbt)
       ▼
┌─────────────┐
│  Snowflake  │
│staging schema│ ← stg_stock_prices (view)
└──────┬──────┘
       │ Transform (dbt)
       ▼
┌──────────────┐
│  Snowflake   │
│analytics     │ ← Technical indicators (tables)
│   schema     │
└──────────────┘
```

## Testing Transformations

### Query Moving Averages
```sql
SELECT 
    symbol,
    date,
    close,
    sma_7,
    sma_20,
    sma_50,
    macd
FROM analytics.stock_moving_averages
WHERE symbol = 'AAPL'
ORDER BY date DESC
LIMIT 10;
```

### Query RSI Signals
```sql
SELECT 
    symbol,
    date,
    close,
    rsi_14,
    rsi_signal
FROM analytics.stock_rsi
WHERE rsi_signal IN ('Overbought', 'Oversold')
ORDER BY date DESC;
```

### Query Combined Indicators
```sql
SELECT 
    symbol,
    date,
    close,
    sma_20,
    rsi_14,
    rsi_signal,
    trend_signal,
    volume_signal
FROM analytics.stock_technical_indicators
WHERE symbol = 'TSLA'
ORDER BY date DESC
LIMIT 20;
```

## Key Changes from ETL to ELT

| What Changed | Before (ETL) | After (ELT) |
|--------------|--------------|-------------|
| Transform location | Python in Airflow | SQL in Snowflake via dbt |
| Raw data | Not stored | Stored in `raw` schema |
| Intermediate data | None | Views in `staging` schema |
| Final data | Simple table | Multiple analytical tables |
| Testing | None | dbt tests |
| Documentation | Code comments | dbt docs |

## Common Commands

```bash
# Run only staging
dbt run --select input.staging.*

# Run only moving averages
dbt run --select stock_moving_averages

# Run only RSI
dbt run --select stock_rsi

# Run combined model and its dependencies
dbt run --select stock_technical_indicators+

# Full refresh (drop and recreate tables)
dbt run --full-refresh

# Generate and view documentation
dbt docs generate && dbt docs serve
```

## Troubleshooting

### Issue: dbt connection fails
```bash
# Check env vars are set
env | grep SNOWFLAKE

# Test connection
dbt debug --profiles-dir .
```

### Issue: Model fails to build
```bash
# Compile to see the generated SQL
dbt compile --profiles-dir . --select model_name

# Check logs
cat logs/dbt.log
```

### Issue: Airflow can't find dbt
```bash
# Install dbt in Airflow's environment
pip install dbt-snowflake

# Or activate Airflow virtualenv first
source $AIRFLOW_HOME/venv/bin/activate
pip install dbt-snowflake
```

## Next Steps

1. **Run the pipeline**:
   ```bash
   # Trigger from Airflow UI or
   airflow dags trigger stock_elt_with_dbt
   ```

2. **Monitor execution**:
   - Check Airflow UI for task status
   - View dbt logs in Airflow task logs

3. **Query results**:
   - Connect to Snowflake
   - Query `analytics` schema tables

4. **Extend transformations**:
   - Add Bollinger Bands
   - Add more technical indicators
   - Create aggregate tables

## Support

- Full documentation: `ELT_SETUP.md`
- dbt docs: https://docs.getdbt.com/
- Airflow docs: https://airflow.apache.org/

---

**Created**: 2025-11-24  
**Purpose**: Convert ETL to ELT using dbt for transformations
