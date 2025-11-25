# End-to-End Data Analytics Pipeline: Stock Market Analysis

A production-ready **ELT (Extract, Load, Transform)** pipeline for real-time stock market analytics, built with **Apache Airflow**, **dbt**, **Snowflake**, and orchestrated via **Docker**.

[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.10.1-017CEE?logo=apache-airflow)](https://airflow.apache.org/)
[![dbt](https://img.shields.io/badge/dbt-1.7.0-FF694B?logo=dbt)](https://www.getdbt.com/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8?logo=snowflake)](https://www.snowflake.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)](https://www.docker.com/)

---

## 📊 System Architecture

<!-- TODO: Add system architecture diagram here -->
**[Architecture Diagram Placeholder]**

*The diagram should illustrate:*
- Data flow from yfinance API → Airflow → Snowflake (Raw Layer)
- Transformation layer: dbt models (Staging → Analytics)
- Orchestration via Airflow DAGs
- Docker containerization
- Optional: BI layer (Superset/Tableau)

---

## 🎯 Project Overview

This project implements a **modern data stack** for stock market analysis with:

- **Real-time data ingestion** from Yahoo Finance API
- **Automated ELT orchestration** with Airflow
- **Data transformation** using dbt with SQL
- **Technical indicators**: Moving Averages (SMA/EMA), RSI, MACD
- **Historical change tracking** via dbt snapshots (SCD Type 2)
- **Containerized deployment** with Docker Compose
- **Production-ready** with error handling, retries, and logging

### Key Features

✅ **Modular Architecture** - Separate ETL and ELT DAGs for clear separation of concerns  
✅ **Technical Analysis** - Built-in financial indicators (RSI, MACD, Moving Averages)  
✅ **Data Quality** - Automated testing with dbt tests  
✅ **Change Tracking** - Slowly Changing Dimensions (SCD Type 2) via snapshots  
✅ **Scalable** - Cloud data warehouse (Snowflake) with serverless compute  
✅ **Reproducible** - Fully containerized with Docker  

---

## 🏗️ Architecture Components

### 1. Data Extraction & Loading (ETL)
- **DAG**: `yfinance_to_snowflake_etl`
- **Schedule**: Weekdays at 6:00 PM UTC
- **Source**: Yahoo Finance API via `yfinance` library
- **Destination**: Snowflake `RAW` schema
- **Features**:
  - Retry logic with exponential backoff
  - Transaction management (BEGIN/COMMIT/ROLLBACK)
  - Multi-symbol support

### 2. Data Transformation (dbt)
- **DAG**: `stock_elt_with_dbt`
- **Schedule**: Weekdays at 6:30 PM UTC (30-minute delay after ETL)
- **Layers**:
  - **Staging**: Data cleaning and validation (`staging.stg_stock_prices`)
  - **Analytics**: Business logic and metrics (`analytics.*`)
- **Models**:
  - `stock_moving_averages` - SMA (7/20/50/200), EMA (12/26), MACD
  - `stock_rsi` - 14-period RSI with overbought/oversold signals
  - `stock_technical_indicators` - Consolidated view with all indicators
- **Snapshots**: Historical tracking of price changes and RSI signals

### 3. Orchestration (Airflow)
- **Version**: Apache Airflow 2.10.1
- **Executor**: LocalExecutor
- **Database**: PostgreSQL 13
- **Port**: http://localhost:8081
- **Authentication**: Basic auth (airflow/airflow)

### 4. Data Warehouse (Snowflake)
- **Schemas**:
  - `RAW` - Landing zone for unprocessed data
  - `STAGING` - Cleaned and validated data
  - `ANALYTICS` - Business-ready metrics and indicators
  - `SNAPSHOTS` - Historical SCD Type 2 tables

---

## 📁 Project Structure

```
end-to-end-data-analytics-snowflake-airflow-dbt-bi/
├── dags/
│   ├── yfinance_to_snowflake_etl.py    # ETL: Extract from API → Load to Snowflake
│   └── stock_elt_with_dbt.py            # ELT: Run dbt transformations
│
├── stock_analytics/                     # dbt project
│   ├── models/
│   │   ├── input/
│   │   │   ├── staging/
│   │   │   │   └── stg_stock_prices.sql      # Staging model
│   │   │   └── _sources.yml                  # Source definitions
│   │   └── output/
│   │       └── core/
│   │           ├── stock_moving_averages.sql  # SMA/EMA/MACD
│   │           ├── stock_rsi.sql              # RSI indicator
│   │           └── stock_technical_indicators.sql  # All indicators
│   ├── snapshots/
│   │   ├── stock_prices_snapshot.sql         # SCD Type 2 for prices
│   │   ├── rsi_signals_snapshot.sql          # SCD Type 2 for RSI
│   │   └── _snapshots.yml
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── packages.yml
│
├── docker-compose.yaml                  # Docker orchestration
├── .env                                 # Environment variables (not in git)
├── pyproject.toml                       # Python dependencies
├── logs/                                # Airflow logs
├── plugins/                             # Airflow plugins
├── config/                              # Airflow config
│
├── README.md                            # This file
├── DOCKER_SETUP.md                      # Docker setup guide
└── SNAPSHOT_IMPLEMENTATION.md           # SCD Type 2 documentation
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
- **Snowflake Account** with credentials
- **4GB+ RAM** and **10GB+ disk space** for Docker

### 1. Clone the Repository

```bash
git clone <repository-url>
cd end-to-end-data-analytics-snowflake-airflow-dbt-bi
```

### 2. Configure Environment Variables

Create a `.env` file from the template:

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

Required variables:
```bash
# Airflow Configuration
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# Snowflake Credentials
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
```

### 3. Configure Airflow Variables

In the Airflow UI (after starting), set these variables:

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `yfinance_symbols` | `AAPL,TSLA,GOOGL,MSFT` | Comma-separated stock symbols |
| `yfinance_time_period` | `180d` | Historical data period |
| `yfinance_interval` | `1d` | Data granularity (1m, 5m, 1h, 1d) |
| `snowflake_userid` | `your_user` | Snowflake username |
| `snowflake_password` | `your_password` | Snowflake password |
| `snowflake_account` | `your_account` | Snowflake account identifier |
| `snowflake_warehouse` | `COMPUTE_WH` | Snowflake warehouse name |
| `snowflake_database` | `STOCK_ANALYTICS` | Target database |
| `snowflake_role` | `ACCOUNTADMIN` | Snowflake role |
| `snowflake_schema` | `RAW` | Raw data schema |

### 4. Start Docker Containers

```bash
# Start all services
docker compose up -d

# Check status
docker ps

# View logs
docker compose logs -f airflow
```

### 5. Access Airflow UI

1. Open browser: http://localhost:8081
2. Login: `airflow` / `airflow`
3. Enable DAGs:
   - `yfinance_to_snowflake_etl`
   - `stock_elt_with_dbt`

### 6. Trigger DAGs Manually

**Option A: Via UI**
- Click the "play" button on each DAG

**Option B: Via CLI**
```bash
# Trigger ETL DAG (loads raw data)
docker exec <container-name> airflow dags trigger yfinance_to_snowflake_etl

# Wait 1-2 minutes, then trigger ELT DAG (runs dbt)
docker exec <container-name> airflow dags trigger stock_elt_with_dbt
```

---

## 📈 Data Models

### Raw Layer (`RAW` schema)

#### `STOCK_PRICE_YFINANCE`
Unprocessed stock data from Yahoo Finance API.

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | VARCHAR(10) | Stock ticker symbol |
| `date` | DATE | Trading date |
| `open` | FLOAT | Opening price |
| `high` | FLOAT | Highest price |
| `low` | FLOAT | Lowest price |
| `close` | FLOAT | Closing price |
| `volume` | FLOAT | Trading volume |

### Staging Layer (`STAGING` schema)

#### `STG_STOCK_PRICES`
Cleaned and validated stock data with derived metrics.

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | VARCHAR | Stock ticker |
| `date` | DATE | Trading date |
| `open` | FLOAT | Opening price |
| `high` | FLOAT | Highest price |
| `low` | FLOAT | Lowest price |
| `close` | FLOAT | Closing price |
| `volume` | FLOAT | Trading volume |
| `daily_range` | FLOAT | High - Low |
| `daily_return_pct` | FLOAT | Percentage return |
| `loaded_at` | TIMESTAMP | ETL timestamp |

### Analytics Layer (`ANALYTICS` schema)

#### `STOCK_MOVING_AVERAGES`
Simple and exponential moving averages with MACD.

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | VARCHAR | Stock ticker |
| `date` | DATE | Trading date |
| `close` | FLOAT | Closing price |
| `sma_7` | FLOAT | 7-day simple moving average |
| `sma_20` | FLOAT | 20-day simple moving average |
| `sma_50` | FLOAT | 50-day simple moving average |
| `sma_200` | FLOAT | 200-day simple moving average |
| `ema_12` | FLOAT | 12-day exponential moving average |
| `ema_26` | FLOAT | 26-day exponential moving average |
| `macd` | FLOAT | MACD (EMA12 - EMA26) |
| `avg_volume_20` | FLOAT | 20-day average volume |

#### `STOCK_RSI`
Relative Strength Index with overbought/oversold signals.

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | VARCHAR | Stock ticker |
| `date` | DATE | Trading date |
| `close` | FLOAT | Closing price |
| `price_change` | FLOAT | Daily price change |
| `rsi_14` | FLOAT | 14-period RSI |
| `rsi_signal` | VARCHAR | Overbought/Oversold/Neutral |

#### `STOCK_TECHNICAL_INDICATORS`
Consolidated view combining all technical indicators.

**Columns**: All columns from staging + moving averages + RSI + trading signals

### Snapshot Layer (`SNAPSHOTS` schema)

#### `STOCK_PRICES_SNAPSHOT`
SCD Type 2 tracking of price changes over time.

#### `RSI_SIGNALS_SNAPSHOT`
SCD Type 2 tracking of RSI signal changes.

---

## 🔧 Development & Testing

### Run dbt Commands Locally

```bash
# Enter Airflow container
docker exec -it <container-name> bash

# Navigate to dbt project
cd /opt/airflow/stock_analytics

# Test connection
dbt debug --profiles-dir .

# Run specific models
dbt run --profiles-dir . --select staging.*
dbt run --profiles-dir . --select output.core.*

# Run tests
dbt test --profiles-dir .

# Create snapshots
dbt snapshot --profiles-dir .

# Exit container
exit
```

### View Data in Snowflake

```sql
-- Check raw data
SELECT * FROM raw.stock_price_yfinance LIMIT 10;

-- Check staging
SELECT * FROM staging.stg_stock_prices LIMIT 10;

-- Check analytics
SELECT * FROM analytics.stock_technical_indicators
WHERE symbol = 'AAPL'
ORDER BY date DESC
LIMIT 10;

-- Check snapshots (SCD Type 2)
SELECT * FROM snapshots.stock_prices_snapshot
WHERE symbol = 'AAPL'
AND dbt_valid_to IS NULL  -- Current records only
LIMIT 10;
```

---

## 📊 BI & Visualization

### Superset Integration (Optional)

Connect Apache Superset to Snowflake to create dashboards:

**Recommended Chart Types:**

1. **Time Series**: Stock prices with moving average overlays
2. **OHLC/Candlestick**: Professional stock charts
3. **RSI Oscillator**: Overbought/oversold indicator with threshold bands
4. **MACD Chart**: Momentum indicator
5. **Volume Analysis**: Bar chart with average volume overlay
6. **Performance Tables**: Latest indicators and signals
7. **Heatmaps**: Volume patterns across multiple stocks

See [SUPERSET_CHARTS.md](SUPERSET_CHARTS.md) for detailed chart configurations.

---

## 🛠️ Troubleshooting

### DAG Fails: dbt not found

```bash
# Check if dbt is installed
docker exec <container-name> dbt --version

# If not, rebuild container
docker compose down
docker compose build
docker compose up -d
```

### DAG Fails: Snowflake connection error

1. Verify `.env` file has correct Snowflake credentials
2. Verify Airflow Variables are set in UI
3. Test connection manually:

```bash
docker exec <container-name> bash
cd /opt/airflow/stock_analytics
dbt debug --profiles-dir .
```

### DAG Fails: dbt_packages directory missing

```bash
# Create directory
docker exec <container-name> mkdir -p /opt/airflow/stock_analytics/dbt_packages

# Retrigger DAG
```

### Permission Errors

```bash
# Fix permissions on host
chmod -R 755 stock_analytics/

# Restart containers
docker compose restart
```

### DAG Not Appearing in UI

```bash
# Check DAG is in correct folder
ls -la dags/

# Force refresh
docker compose exec airflow airflow dags reserialize

# Check logs
docker compose logs -f airflow | grep -i error
```

---

## 📅 Scheduled Execution

Both DAGs run automatically on weekdays:

| DAG | Schedule | Cron | Description |
|-----|----------|------|-------------|
| `yfinance_to_snowflake_etl` | 6:00 PM UTC | `0 18 * * 1-5` | Extract & load raw data |
| `stock_elt_with_dbt` | 6:30 PM UTC | `30 18 * * 1-5` | Transform with dbt |

**Execution Flow:**
```
18:00 → ETL DAG starts → Fetches data from yfinance → Loads to RAW schema
18:00-18:30 → Processing & validation
18:30 → ELT DAG starts → Validates raw data exists → Runs dbt transformations
18:30-18:32 → dbt staging models → dbt core models → snapshots → tests
```

---

## 🧪 Testing

### Unit Tests (dbt)

```bash
# Run all tests
dbt test --profiles-dir .

# Run specific test
dbt test --profiles-dir . --select stg_stock_prices
```

### Integration Tests

```bash
# Trigger full pipeline manually
docker exec <container-name> airflow dags trigger yfinance_to_snowflake_etl
sleep 60
docker exec <container-name> airflow dags trigger stock_elt_with_dbt

# Check results in Snowflake
```

---

## 🔒 Security Best Practices

1. ✅ **Never commit** `.env` file to version control
2. ✅ Use **Airflow Connections** for sensitive credentials
3. ✅ Rotate **Snowflake passwords** regularly
4. ✅ Use **role-based access control** (RBAC) in Snowflake
5. ✅ Enable **SSL/TLS** for Snowflake connections in production
6. ✅ Use **secrets management** (AWS Secrets Manager, Vault) for production

---

## 📚 Additional Documentation

- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Detailed Docker setup and troubleshooting
- [SNAPSHOT_IMPLEMENTATION.md](SNAPSHOT_IMPLEMENTATION.md) - Guide to dbt snapshots (SCD Type 2)
- [stock_analytics/README.md](stock_analytics/README.md) - dbt project documentation
- [stock_analytics/ELT_SETUP.md](stock_analytics/ELT_SETUP.md) - ELT architecture details

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Apache Airflow** - Workflow orchestration
- **dbt Labs** - Data transformation framework
- **Snowflake** - Cloud data warehouse
- **yfinance** - Yahoo Finance API wrapper
- **Docker** - Containerization platform

---

## 📧 Contact

For questions or support, please open an issue in the GitHub repository.

---

**Built with ❤️ for modern data engineering**
