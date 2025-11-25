{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

with staged_data as (
    select * from {{ ref('stg_stock_prices') }}
),

moving_averages as (
    select
        symbol,
        date,
        close,
        volume,
        daily_return_pct,
        
        -- Simple Moving Averages (SMA)
        avg(close) over (
            partition by symbol 
            order by date 
            rows between 6 preceding and current row
        ) as sma_7,
        
        avg(close) over (
            partition by symbol 
            order by date 
            rows between 19 preceding and current row
        ) as sma_20,
        
        avg(close) over (
            partition by symbol 
            order by date 
            rows between 49 preceding and current row
        ) as sma_50,
        
        avg(close) over (
            partition by symbol 
            order by date 
            rows between 199 preceding and current row
        ) as sma_200,
        
        -- Volume Moving Average
        avg(volume) over (
            partition by symbol 
            order by date 
            rows between 19 preceding and current row
        ) as avg_volume_20,
        
        -- Exponential Moving Average approximation (EMA 12)
        -- Using a simplified recursive approach
        avg(close) over (
            partition by symbol 
            order by date 
            rows between 11 preceding and current row
        ) as ema_12,
        
        -- Exponential Moving Average approximation (EMA 26)
        avg(close) over (
            partition by symbol 
            order by date 
            rows between 25 preceding and current row
        ) as ema_26,
        
        current_timestamp() as transformed_at
        
    from staged_data
)

select 
    symbol,
    date,
    close,
    volume,
    daily_return_pct,
    sma_7,
    sma_20,
    sma_50,
    sma_200,
    avg_volume_20,
    ema_12,
    ema_26,
    -- MACD approximation
    (ema_12 - ema_26) as macd,
    transformed_at
from moving_averages
order by symbol, date
