from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import time

# --- Snowflake connection parameters from Airflow Variables ---
USER_ID = Variable.get("snowflake_userid")
PASSWORD = Variable.get("snowflake_password")
ACCOUNT = Variable.get("snowflake_account")
WAREHOUSE = Variable.get("snowflake_warehouse")
DATABASE = Variable.get("snowflake_database")
ROLE = Variable.get("snowflake_role")
RAW_SCHEMA = Variable.get("snowflake_schema")

# --- dbt project path ---
DBT_PROJECT_DIR = "/Users/aakashvardhan/Documents/end-to-end-data-analytics-snowflake-airflow-dbt-bi/stock_analytics"


def return_snowflake_hook():
    hook = SnowflakeHook(snowflake_conn_id='snowflake_conn')
    conn = hook.get_conn()
    return conn


def get_stock_data(symbol, period, interval, max_retries=2, backoff=2.0):
    for attempt in range(max_retries):
        try:
            stock_data = yf.download(
                symbol, period=period, interval=interval, group_by=symbol
            )

            if isinstance(stock_data.columns, pd.MultiIndex):
                if symbol in stock_data.columns.get_level_values(0):
                    stock_data = stock_data.xs(symbol, axis=1, level=0)

            if stock_data.empty:
                print(f"No data available for symbol {symbol}")
                return None
            
            print(f"Successfully downloaded {len(stock_data)} rows for {symbol}")
            return stock_data
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"Max retries reached. Unable to download stock data for {symbol}.")
                return None


@task
def extract(symbols, period, interval):
    """Extract stock data from yfinance API"""
    print(f"Starting extraction for symbols: {symbols}")
    print(f"Period: {period}, Interval: {interval}")
    
    results = []
    for symbol in symbols:
        try:
            data = get_stock_data(symbol, period, interval)
            
            if data is None or data.empty:
                print(f"Skipping {symbol} - no data returned")
                continue

            data = data.reset_index()
            date_col = "Date" if "Date" in data.columns else "index"
            data = data.rename(columns={date_col: "date"})
            data = data[["date", "Open", "High", "Low", "Close", "Volume"]]

            for row in data.itertuples(index=False):
                results.append(
                    {
                        "symbol": symbol,
                        "date": row.date.strftime("%Y-%m-%d"),
                        "open": float(row.Open),
                        "high": float(row.High),
                        "low": float(row.Low),
                        "close": float(row.Close),
                        "volume": float(row.Volume),
                    }
                )
            print(f"Extracted {len(data)} rows for {symbol}")
        except Exception as e:
            print(f"Error processing symbol {symbol}: {e}")

    print(f"Total records extracted: {len(results)}")
    return results


@task
def load_to_snowflake(records, con):
    """Load raw data to Snowflake (ELT - Extract and Load only)"""
    cursor = con.cursor()
    target_table = f"{DATABASE}.raw.STOCK_PRICE_YFINANCE"
    
    try:
        cursor.execute("BEGIN;")
        cursor.execute(f"""
            CREATE OR REPLACE TABLE {target_table} (
                symbol VARCHAR(10),
                date DATE,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume FLOAT,
                PRIMARY KEY (symbol, date)
            );
        """)
        
        # Convert to list of tuples for executemany
        records_tuples = [
            (r["symbol"], r["date"], r["open"], r["high"], r["low"], r["close"], r["volume"])
            for r in records
        ]
        
        cursor.executemany(f"""
            INSERT INTO {target_table} (symbol, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, records_tuples)
        
        cursor.execute("COMMIT;")
        print(f"Loaded {len(records)} records to {target_table}")
    except Exception as e:
        cursor.execute("ROLLBACK;")
        raise e


with DAG(
    dag_id="stock_elt_with_dbt",
    start_date=datetime(2025, 11, 20),
    tags=["ELT", "dbt", "stock_analytics"],
    catchup=False,
    schedule="0 18 * * 1-5",  # Run weekdays at 6 PM
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:

    raw_symbols = Variable.get("yfinance_symbols")
    SYMBOLS = [s.strip() for s in raw_symbols.split(",") if s.strip()]
    PERIOD = Variable.get("yfinance_time_period")
    INTERVAL = Variable.get("yfinance_interval")

    snowflake_conn = return_snowflake_hook()
    
    # Step 1: Extract from yfinance
    extracted_data = extract(SYMBOLS, PERIOD, INTERVAL)
    
    # Step 2: Load to Snowflake (no transformation in Airflow)
    load_task = load_to_snowflake(extracted_data, snowflake_conn)
    
    # Step 3: Run dbt transformations
    with TaskGroup("dbt_transformations") as dbt_group:
        
        # Run dbt deps (install dependencies)
        dbt_deps = BashOperator(
            task_id="dbt_deps",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps --profiles-dir .",
        )
        
        # Run dbt debug (test connection)
        dbt_debug = BashOperator(
            task_id="dbt_debug",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt debug --profiles-dir .",
        )
        
        # Run staging models
        dbt_run_staging = BashOperator(
            task_id="dbt_run_staging",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --profiles-dir . --select input.staging.*",
        )
        
        # Run core models (technical indicators)
        dbt_run_core = BashOperator(
            task_id="dbt_run_core",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --profiles-dir . --select output.core.*",
        )
        
        # Test dbt models
        dbt_test = BashOperator(
            task_id="dbt_test",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --profiles-dir .",
        )
        
        # Define task dependencies within dbt group
        dbt_deps >> dbt_debug >> dbt_run_staging >> dbt_run_core >> dbt_test
    
    # Overall DAG dependencies
    extracted_data >> load_task >> dbt_group
