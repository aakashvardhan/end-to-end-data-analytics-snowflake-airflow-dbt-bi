# dags/stock_elt_with_dbt.py
from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

from datetime import datetime, timedelta

# --- Snowflake connection parameters from Airflow Variables ---
DATABASE = Variable.get("snowflake_database")

# --- dbt project path ---
DBT_PROJECT_DIR = "/opt/airflow/stock_analytics"


def return_snowflake_hook():
    hook = SnowflakeHook(snowflake_conn_id='snowflake_conn')
    conn = hook.get_conn()
    return conn


@task
def validate_raw_data(con):
    """Validate that raw data exists in Snowflake before running dbt"""
    cursor = con.cursor()
    target_table = f"{DATABASE}.raw.STOCK_PRICE_YFINANCE"
    
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        count = cursor.fetchone()[0]
        print(f"Found {count} records in {target_table}")
        
        if count == 0:
            raise ValueError(f"No data found in {target_table}. Please run yfinance_to_snowflake_etl DAG first.")
        
        return count
    except Exception as e:
        print(f"Error validating raw data: {e}")
        raise e


with DAG(
    dag_id="stock_elt_with_dbt",
    start_date=datetime(2025, 11, 20),
    tags=["ELT", "dbt", "stock_analytics"],
    catchup=False,
    schedule="30 18 * * 1-5",  # Run weekdays at 6:30 PM (30 min after ETL DAG)
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:

    snowflake_conn = return_snowflake_hook()
    
    # Step 1: Validate raw data exists (loaded by yfinance_to_snowflake_etl DAG)
    validate_task = validate_raw_data(snowflake_conn)
    
    # Step 2: Run dbt transformations on existing raw data
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
        
        # Run dbt snapshots (capture historical changes)
        dbt_snapshot = BashOperator(
            task_id="dbt_snapshot",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt snapshot --profiles-dir .",
        )
        
        # Test dbt models
        dbt_test = BashOperator(
            task_id="dbt_test",
            bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --profiles-dir .",
        )
        
        # Define task dependencies within dbt group
        dbt_deps >> dbt_debug >> dbt_run_staging >> dbt_run_core >> dbt_snapshot >> dbt_test
    
    # Overall DAG dependencies
    validate_task >> dbt_group
