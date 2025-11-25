# Snapshot Implementation Summary

## ✅ Changes Made

### 1. Updated Airflow DAG
**File**: `dags/stock_elt_with_dbt.py`

Added `dbt_snapshot` task to the pipeline:
```python
dbt_snapshot = BashOperator(
    task_id="dbt_snapshot",
    bash_command=f"cd {DBT_PROJECT_DIR} && dbt snapshot --profiles-dir .",
)
```

**New Pipeline Flow**:
```
extract → load → dbt_deps → dbt_debug → dbt_run_staging → dbt_run_core → dbt_snapshot → dbt_test
```

### 2. Created Snapshot Files

#### Stock Prices Snapshot
**File**: `stock_analytics/snapshots/stock_prices_snapshot.sql`
- **Schema**: `SNAPSHOTS`
- **Source**: `stg_stock_prices`
- **Strategy**: Check columns for changes
- **Tracked Columns**: `close`, `volume`, `high`, `low`
- **Purpose**: Track price adjustments and corrections

#### RSI Signals Snapshot
**File**: `stock_analytics/snapshots/rsi_signals_snapshot.sql`
- **Schema**: `SNAPSHOTS`
- **Source**: `stock_rsi`
- **Strategy**: Check columns for changes
- **Tracked Columns**: `rsi_14`, `rsi_signal`
- **Purpose**: Track overbought/oversold signal changes
- **Filter**: Only captures Overbought and Oversold signals

### 3. Documentation
**Files Created**:
- `stock_analytics/snapshots/_snapshots.yml` - Snapshot schema documentation
- `stock_analytics/SNAPSHOTS_GUIDE.md` - Comprehensive guide on using snapshots

## What Are Snapshots?

Snapshots implement **Type 2 Slowly Changing Dimensions (SCD)** to track historical changes. Each snapshot run:
1. Compares current data with previous snapshot
2. Marks changed records as historical (sets `dbt_valid_to`)
3. Inserts new versions (sets `dbt_valid_from`)

### Metadata Columns Added

| Column | Description |
|--------|-------------|
| `dbt_scd_id` | Unique ID for each snapshot record |
| `dbt_updated_at` | Last update timestamp |
| `dbt_valid_from` | When this version became valid |
| `dbt_valid_to` | When this version became invalid (NULL = current) |

## Snowflake Schema Structure

```
TRAINING_DB
├── RAW
│   └── STOCK_PRICE_YFINANCE (raw data)
├── STAGING
│   └── stg_stock_prices (view)
├── ANALYTICS
│   ├── stock_moving_averages (table)
│   ├── stock_rsi (table)
│   └── stock_technical_indicators (table)
└── SNAPSHOTS (NEW!)
    ├── stock_prices_snapshot (table)
    └── rsi_signals_snapshot (table)
```

## Testing

Snapshots were successfully tested:
```bash
✅ 2 of 2 OK snapshotted snapshots.stock_prices_snapshot
✅ 1 of 2 OK snapshotted snapshots.rsi_signals_snapshot
```

## Next DAG Run

The next time `stock_elt_with_dbt` runs, it will:
1. Extract stock data
2. Load to RAW schema
3. Create/update staging views
4. Create/update analytics tables
5. **Run snapshots** (NEW!)
6. Run tests

## Querying Snapshot Data

### Current Records
```sql
SELECT * FROM TRAINING_DB.SNAPSHOTS.stock_prices_snapshot
WHERE dbt_valid_to IS NULL;
```

### Historical Records
```sql
SELECT * FROM TRAINING_DB.SNAPSHOTS.stock_prices_snapshot
WHERE dbt_valid_to IS NOT NULL
ORDER BY symbol, date, dbt_valid_from;
```

### Track Price Adjustments
```sql
SELECT 
    symbol,
    date,
    close,
    lag(close) OVER (PARTITION BY symbol, date ORDER BY dbt_valid_from) as previous_close,
    dbt_valid_from,
    dbt_valid_to
FROM TRAINING_DB.SNAPSHOTS.stock_prices_snapshot
WHERE symbol = 'AAPL'
ORDER BY date DESC, dbt_valid_from DESC;
```

## Benefits

1. **Audit Trail**: See all historical changes
2. **Data Quality**: Detect unexpected adjustments
3. **Compliance**: Maintain historical records
4. **Analysis**: Analyze how data changes over time

## Use Cases

### Stock Prices Snapshot
- Track stock splits and adjustments
- Detect data corrections from source
- Maintain audit trail for compliance
- Analyze price revision patterns

### RSI Signals Snapshot
- Track when stocks enter/exit signals
- Analyze signal duration
- Backtest signal performance
- Monitor signal frequency changes

## Running Manually

### In Docker Container
```bash
docker compose exec airflow bash -c 'cd /opt/airflow/stock_analytics && dbt snapshot --profiles-dir .'
```

### View Logs
```bash
docker compose logs airflow | grep snapshot
```

## Documentation

Full documentation available in:
- `stock_analytics/SNAPSHOTS_GUIDE.md` - Complete guide
- `stock_analytics/snapshots/_snapshots.yml` - Schema docs

## Summary

✅ **DAG Updated**: Added dbt_snapshot task
✅ **2 Snapshots Created**: stock_prices and rsi_signals
✅ **Documentation Created**: Complete guide and schema docs
✅ **Tested Successfully**: Both snapshots running in SNAPSHOTS schema
✅ **Pipeline Enhanced**: Now tracks historical changes automatically

---

**Next Steps**:
1. Trigger DAG to run full pipeline with snapshots
2. Check TRAINING_DB.SNAPSHOTS schema in Snowflake
3. Query snapshot tables to see historical tracking
4. Monitor snapshot growth over time
