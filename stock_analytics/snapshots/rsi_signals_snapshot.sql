{% snapshot rsi_signals_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='symbol||\'-\'||date',
      strategy='check',
      check_cols=['rsi_14', 'rsi_signal'],
      invalidate_hard_deletes=True
    )
}}

select 
    symbol,
    date,
    close,
    price_change,
    rsi_14,
    rsi_signal
from {{ ref('stock_rsi') }}
where rsi_signal IN ('Overbought', 'Oversold')

{% endsnapshot %}
