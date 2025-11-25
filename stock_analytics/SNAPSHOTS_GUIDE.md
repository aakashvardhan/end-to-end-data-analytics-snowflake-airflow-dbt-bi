# dbt Snapshots Guide

## Overview
Snapshots in dbt implement **Type 2 Slowly Changing Dimensions (SCD)** to track historical changes in your data over time.

## What Are Snapshots?

Snapshots capture the state of your mutable tables and track how they change. Each time you run `dbt snapshot`, dbt:
1. Compares current data with the previous snapshot
2. Identifies changed records
3. Marks old records as historical with `dbt_valid_to` timestamp
4. Inserts new versions with `dbt_valid_from` timestamp

## Snapshots in This Project

### 1. Stock Prices Snapshot
**Location**: `snapshots/stock_prices_snapshot.sql`
**Target Schema**: `SNAPSHOTS`
**Source**: `stg_stock_prices`

**Tracks changes in**:
- `close` - Closing price
- `volume` - Trading volume
- `high` - Highest price
- `low` - Lowest price

**Use Case**: Stock prices can be adjusted retroactively (e.g., for splits, dividends). This snapshot helps track these adjustments.

### 2. RSI Signals Snapshot
**Location**: `snapshots/rsi_signals_snapshot.sql`
**Target Schema**: `SNAPSHOTS`
**Source**: `stock_rsi`

**Tracks changes in**:
- `rsi_14` - RSI value
- `rsi_signal` - Overbought/Oversold signal

**Use Case**: Track when stocks enter/exit overbought or oversold conditions for signal analysis.

## How Snapshots Work

### Check Strategy
Both snapshots use the `check` strategy, which monitors specific columns for changes:

```sql
config(
  strategy='check',
  check_cols=['close', 'volume', 'high', 'low']
)
```

When any of these columns change, dbt creates a new snapshot record.

### Metadata Columns
dbt automatically adds these columns to snapshot tables:

| Column | Description |
|--------|-------------|
| `dbt_scd_id` | Unique identifier for each snapshot record |
| `dbt_updated_at` | When this record was last updated |
| `dbt_valid_from` | When this version became valid |
| `dbt_valid_to` | When this version became invalid (NULL = current) |

## Running Snapshots

### Via Airflow DAG
Snapshots run automatically as part of the `stock_elt_with_dbt` DAG:
```
extract → load → staging → core models → snapshots → tests
```

### Manually in Container
```bash
docker compose exec airflow bash -c 'cd /opt/airflow/stock_analytics && dbt snapshot --profiles-dir .'
```

### From Host (if dbt installed locally)
```bash
cd stock_analytics
dbt snapshot --profiles-dir .
```

## Querying Snapshot Data

### Get Current (Active) Records
```sql
SELECT 
    symbol,
    date,
    close,
    volume,
    rsi_14,
    rsi_signal,
    dbt_valid_from,
    dbt_updated_at
FROM snapshots.stock_prices_snapshot
WHERE dbt_valid_to IS NULL;
```

### Get Historical Records
```sql
SELECT 
    symbol,
    date,
    close,
    dbt_valid_from,
    dbt_valid_to,
    datediff('day', dbt_valid_from, dbt_valid_to) as days_valid
FROM snapshots.stock_prices_snapshot
WHERE dbt_valid_to IS NOT NULL
ORDER BY symbol, date, dbt_valid_from;
```

### Track Changes Over Time
```sql
SELECT 
    symbol,
    date,
    close,
    lag(close) OVER (PARTITION BY symbol, date ORDER BY dbt_valid_from) as previous_close,
    close - lag(close) OVER (PARTITION BY symbol, date ORDER BY dbt_valid_from) as price_adjustment,
    dbt_valid_from,
    dbt_valid_to
FROM snapshots.stock_prices_snapshot
WHERE symbol = 'AAPL'
ORDER BY date DESC, dbt_valid_from DESC
LIMIT 20;
```

### RSI Signal History
```sql
-- See when stocks entered/exited overbought/oversold
SELECT 
    symbol,
    date,
    rsi_14,
    rsi_signal,
    dbt_valid_from,
    dbt_valid_to,
    CASE 
        WHEN dbt_valid_to IS NULL THEN 'CURRENT'
        ELSE 'HISTORICAL'
    END as status
FROM snapshots.rsi_signals_snapshot
WHERE symbol = 'TSLA'
ORDER BY date DESC, dbt_valid_from DESC
LIMIT 20;
```

## Snapshot Lifecycle Example

### Initial Run (Day 1)
```
symbol | date       | close | dbt_valid_from | dbt_valid_to
-------|------------|-------|----------------|-------------
AAPL   | 2025-11-24 | 195.0 | 2025-11-24     | NULL
```

### Second Run (Day 2) - No Change
No new records created if data hasn't changed.

### Third Run (Day 3) - Price Adjusted
```
symbol | date       | close | dbt_valid_from | dbt_valid_to
-------|------------|-------|----------------|-------------
AAPL   | 2025-11-24 | 195.0 | 2025-11-24     | 2025-11-26
AAPL   | 2025-11-24 | 195.5 | 2025-11-26     | NULL
```

The old record is marked invalid, and a new record captures the adjustment.

## Benefits

1. **Audit Trail**: See all historical changes to your data
2. **Data Quality**: Detect unexpected changes or adjustments
3. **Analysis**: Analyze how adjustments impact metrics
4. **Compliance**: Maintain historical records for regulatory requirements

## Best Practices

1. **Run Regularly**: Snapshots should run on the same schedule as your data updates
2. **Monitor Size**: Snapshots grow over time; archive old records if needed
3. **Document Changes**: Add notes in dbt docs about what changes you expect to see
4. **Test Snapshots**: Use dbt tests to ensure snapshot logic works correctly

## Troubleshooting

### Snapshot Table Already Exists
If you need to rebuild snapshots:
```sql
DROP TABLE IF EXISTS snapshots.stock_prices_snapshot;
DROP TABLE IF EXISTS snapshots.rsi_signals_snapshot;
```

Then run `dbt snapshot` again.

### Too Many Historical Records
Archive old records:
```sql
-- Archive records older than 1 year
CREATE TABLE snapshots.stock_prices_snapshot_archive AS
SELECT * FROM snapshots.stock_prices_snapshot
WHERE dbt_valid_to < dateadd('year', -1, current_timestamp());

-- Delete archived records
DELETE FROM snapshots.stock_prices_snapshot
WHERE dbt_valid_to < dateadd('year', -1, current_timestamp());
```

## Next Steps

1. Monitor snapshot tables in Snowflake after each DAG run
2. Create dashboards to visualize data changes over time
3. Add more snapshots for other tables as needed
4. Set up alerts for unexpected changes

---

**Note**: The first snapshot run creates the baseline. Subsequent runs track changes from that baseline.
