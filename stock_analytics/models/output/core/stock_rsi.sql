{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

with staged_data as (
    select * from {{ ref('stg_stock_prices') }}
),

price_changes as (
    select
        symbol,
        date,
        close,
        -- Calculate price change from previous day
        close - lag(close, 1) over (partition by symbol order by date) as price_change
    from staged_data
),

gains_losses as (
    select
        symbol,
        date,
        close,
        price_change,
        -- Separate gains and losses
        case when price_change > 0 then price_change else 0 end as gain,
        case when price_change < 0 then abs(price_change) else 0 end as loss
    from price_changes
),

average_gains_losses as (
    select
        symbol,
        date,
        close,
        price_change,
        gain,
        loss,
        -- Calculate 14-period average gains and losses
        avg(gain) over (
            partition by symbol 
            order by date 
            rows between 13 preceding and current row
        ) as avg_gain_14,
        
        avg(loss) over (
            partition by symbol 
            order by date 
            rows between 13 preceding and current row
        ) as avg_loss_14
    from gains_losses
),

rsi_calculation as (
    select
        symbol,
        date,
        close,
        price_change,
        avg_gain_14,
        avg_loss_14,
        -- Calculate Relative Strength (RS)
        case 
            when avg_loss_14 = 0 then null
            else avg_gain_14 / nullif(avg_loss_14, 0)
        end as rs,
        -- Calculate RSI
        case 
            when avg_loss_14 = 0 then 100
            else 100 - (100 / (1 + (avg_gain_14 / nullif(avg_loss_14, 0))))
        end as rsi_14,
        
        current_timestamp() as transformed_at
    from average_gains_losses
)

select
    symbol,
    date,
    close,
    price_change,
    rsi_14,
    -- RSI signal interpretation
    case
        when rsi_14 >= 70 then 'Overbought'
        when rsi_14 <= 30 then 'Oversold'
        else 'Neutral'
    end as rsi_signal,
    transformed_at
from rsi_calculation
where rsi_14 is not null
order by symbol, date
