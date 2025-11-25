{% snapshot stock_prices_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='symbol||\'-\'||date',
      strategy='check',
      check_cols=['close', 'volume', 'high', 'low'],
      invalidate_hard_deletes=True
    )
}}

select 
    symbol,
    date,
    open,
    high,
    low,
    close,
    volume,
    daily_range,
    daily_return_pct,
    loaded_at
from {{ ref('stg_stock_prices') }}

{% endsnapshot %}
