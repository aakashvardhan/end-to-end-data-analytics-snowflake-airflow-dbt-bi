{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

with base_prices as (
    select * from {{ ref('stg_stock_prices') }}
),

moving_avg as (
    select 
        symbol,
        date,
        sma_7,
        sma_20,
        sma_50,
        sma_200,
        ema_12,
        ema_26,
        macd,
        avg_volume_20
    from {{ ref('stock_moving_averages') }}
),

rsi_data as (
    select
        symbol,
        date,
        rsi_14,
        rsi_signal
    from {{ ref('stock_rsi') }}
)

select
    bp.symbol,
    bp.date,
    bp.open,
    bp.high,
    bp.low,
    bp.close,
    bp.volume,
    bp.daily_range,
    bp.daily_return_pct,
    
    -- Moving averages
    ma.sma_7,
    ma.sma_20,
    ma.sma_50,
    ma.sma_200,
    ma.ema_12,
    ma.ema_26,
    ma.macd,
    ma.avg_volume_20,
    
    -- RSI
    r.rsi_14,
    r.rsi_signal,
    
    -- Trading signals
    case 
        when ma.sma_7 > ma.sma_20 then 'Bullish'
        when ma.sma_7 < ma.sma_20 then 'Bearish'
        else 'Neutral'
    end as trend_signal,
    
    case
        when bp.volume > ma.avg_volume_20 then 'High Volume'
        else 'Normal Volume'
    end as volume_signal,
    
    current_timestamp() as created_at
    
from base_prices bp
left join moving_avg ma 
    on bp.symbol = ma.symbol 
    and bp.date = ma.date
left join rsi_data r 
    on bp.symbol = r.symbol 
    and bp.date = r.date
order by bp.symbol, bp.date
