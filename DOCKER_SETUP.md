# Docker Setup for Stock Analytics ELT Pipeline

## Issue Fixed

The error occurred because Airflow runs inside a Docker container and couldn't access the local macOS path `/Users/aakashvardhan/...`.

### Changes Made:

1. **Added volume mount** in `docker-compose.yaml`:
   - Mounts `stock_analytics` folder into container at `/opt/airflow/stock_analytics`

2. **Updated DAG path** in `stock_elt_with_dbt.py`:
   - Changed from local path to container path: `/opt/airflow/stock_analytics`

3. **Added Snowflake environment variables** to `docker-compose.yaml`:
   - Makes Snowflake credentials available to dbt inside container

4. **Created `.env.example`** file:
   - Template for environment variables

## Setup Steps

### Step 1: Create .env file

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual Snowflake credentials
nano .env
```

Update these values in `.env`:
```bash
SNOWFLAKE_ACCOUNT=your_actual_account
SNOWFLAKE_USER=your_actual_user
SNOWFLAKE_PASSWORD=your_actual_password
SNOWFLAKE_ROLE=your_actual_role
SNOWFLAKE_WAREHOUSE=your_actual_warehouse
SNOWFLAKE_DATABASE=your_actual_database
```

### Step 2: Restart Docker Compose

```bash
# Stop current containers
docker compose down

# Rebuild and start (to pick up new volumes and env vars)
docker compose up -d

# Check logs
docker compose logs -f airflow
```

### Step 3: Verify dbt is installed in container

```bash
# Enter the Airflow container
docker compose exec airflow bash

# Check dbt version
dbt --version

# Navigate to dbt project
cd /opt/airflow/stock_analytics

# Test dbt connection
dbt debug --profiles-dir .

# Exit container
exit
```

### Step 4: Trigger the DAG

1. Open Airflow UI: http://localhost:8081
2. Login with username: `airflow`, password: `airflow`
3. Find the DAG: `stock_elt_with_dbt`
4. Enable it (toggle switch)
5. Trigger manually (play button)

## Project Structure in Container

```
/opt/airflow/
├── dags/
│   ├── yfinance_to_snowflake_etl.py
│   └── stock_elt_with_dbt.py
├── logs/
├── config/
├── plugins/
└── stock_analytics/           # <-- dbt project mounted here
    ├── models/
    │   ├── input/
    │   └── output/
    ├── dbt_project.yml
    ├── profiles.yml
    └── ...
```

## Troubleshooting

### Issue: dbt not found
```bash
# Enter container
docker compose exec airflow bash

# Install dbt manually (if not already installed)
pip install dbt-snowflake

# Or rebuild container
docker compose down
docker compose build
docker compose up -d
```

### Issue: Permission errors
```bash
# Fix permissions on host machine
chmod -R 755 stock_analytics/

# Restart containers
docker compose restart
```

### Issue: Environment variables not set
```bash
# Check if env vars are set in container
docker compose exec airflow bash
env | grep SNOWFLAKE

# If not set, check .env file exists and restart
docker compose down
docker compose up -d
```

### Issue: Volume not mounted
```bash
# Check volumes are mounted
docker compose exec airflow ls -la /opt/airflow/

# Should see stock_analytics folder
# If not, check docker-compose.yaml and restart
```

### Issue: Stale DAG code
```bash
# Airflow auto-reloads DAGs, but you can force refresh
docker compose restart airflow

# Or clear cache
docker compose exec airflow airflow dags reserialize
```

## Testing dbt Inside Container

```bash
# Enter container
docker compose exec airflow bash

# Navigate to dbt project
cd /opt/airflow/stock_analytics

# Run dbt commands
dbt debug --profiles-dir .
dbt compile --profiles-dir .
dbt run --profiles-dir . --select input.staging.*
dbt run --profiles-dir . --select output.core.*
dbt test --profiles-dir .

# Exit
exit
```

## Alternative: Run dbt from Host (Optional)

If you want to run dbt from your Mac without Docker:

```bash
# Install dbt on your Mac
pip install dbt-snowflake

# Set environment variables on your Mac
export SNOWFLAKE_ACCOUNT="..."
export SNOWFLAKE_USER="..."
export SNOWFLAKE_PASSWORD="..."
export SNOWFLAKE_ROLE="..."
export SNOWFLAKE_WAREHOUSE="..."
export SNOWFLAKE_DATABASE="..."

# Navigate to dbt project
cd stock_analytics

# Run dbt
dbt run --profiles-dir .
```

But for Airflow orchestration, dbt must run inside the container.

## Verifying the Fix

After restarting Docker Compose:

1. Check the DAG runs successfully:
   ```bash
   docker compose logs -f airflow | grep stock_elt_with_dbt
   ```

2. Check dbt tasks specifically:
   ```bash
   docker compose logs -f airflow | grep dbt_transformations
   ```

3. Look for successful completion messages:
   - `dbt deps` should complete
   - `dbt debug` should show successful connection
   - `dbt run` should build models

## Quick Commands Reference

```bash
# Stop all containers
docker compose down

# Start all containers
docker compose up -d

# View logs
docker compose logs -f

# View only Airflow logs
docker compose logs -f airflow

# Enter Airflow container
docker compose exec airflow bash

# Restart just Airflow
docker compose restart airflow

# Rebuild everything
docker compose down
docker compose build
docker compose up -d
```

## Next Steps

Once the DAG runs successfully:

1. **Check Snowflake** to verify data in:
   - `raw.stock_price_yfinance` (raw data)
   - `staging.stg_stock_prices` (staging view)
   - `analytics.stock_moving_averages` (technical indicators)
   - `analytics.stock_rsi` (RSI data)
   - `analytics.stock_technical_indicators` (combined)

2. **Monitor future runs** on the schedule (weekdays at 6 PM)

3. **Extend the pipeline** by adding more dbt models

---

**Key Point**: The dbt project path in the DAG is now `/opt/airflow/stock_analytics` (container path), not the local macOS path.
