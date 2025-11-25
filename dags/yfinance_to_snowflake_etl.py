# dags/yfinance_to_snowflake_etl.py
from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from datetime import datetime
import yfinance as yf
import pandas as pd
import time

# --- Snowflake connection parameters from Airflow Variables ---
DATABASE = Variable.get("snowflake_database")



def return_snowflake_hook():
    hook = SnowflakeHook(
        snowflake_conn_id='snowflake_conn'
    )
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
def transform(price_list):
    print(f"Transforming {len(price_list)} records")
    transformed_list = []
    for price in price_list:
        transformed_list.append(
            [
                price["symbol"],
                price["date"],
                price["open"],
                price["high"],
                price["low"],
                price["close"],
                price["volume"],
            ]
        )
    return transformed_list

@task
def load_many(records, con):
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
        
        cursor.executemany(f"""
            INSERT INTO {target_table} (symbol, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, records)
        
        cursor.execute("COMMIT;")
        print(f"Successfully loaded {len(records)} records to {target_table}")
    except Exception as e:
        cursor.execute("ROLLBACK;")
        print(f"Failed to load data: {e}")
        raise e

with DAG(
    dag_id="yfinance_to_snowflake_etl",
    start_date=datetime(2025, 11, 20),
    tags=["ETL"],
    catchup=False,
    schedule="0 18 * * 1-5",  # Run weekdays at 6:00 PM
) as dag:

    raw_symbols = Variable.get("yfinance_symbols")  # "AAPL,TSLA"
    SYMBOLS = [s.strip() for s in raw_symbols.split(",") if s.strip()]  # ["AAPL", "TSLA"]
    PERIOD = Variable.get("yfinance_time_period")  # "180d"
    INTERVAL = Variable.get("yfinance_interval")  # "1d"

    snowflake_conn = return_snowflake_hook()
    extracted_data = extract(SYMBOLS, PERIOD, INTERVAL)
    transformed_data = transform(extracted_data)
    load_many(transformed_data, snowflake_conn)
