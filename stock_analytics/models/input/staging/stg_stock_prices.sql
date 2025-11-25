{{
    config(
        materialized='view',
        schema='staging'
    )
}}

with source as (
    select * from {{ source('raw_data', 'stock_price_yfinance') }}
),

cleaned as (
    select
        symbol,
        date,
        open,
        high,
        low,
        close,
        volume,
        -- Add derived fields
        (high - low) as daily_range,
        ((close - open) / nullif(open, 0)) * 100 as daily_return_pct,
        -- Add metadata
        current_timestamp() as loaded_at
    from source
    where 
        -- Data quality filters
        open > 0
        and high > 0
        and low > 0
        and close > 0
        and volume >= 0
        and high >= low
        and date is not null
)

select * from cleaned
