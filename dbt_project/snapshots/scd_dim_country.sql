-- snapshots/scd_dim_country.sql
-- SCD Type 2 on the country dimension.
-- Tracks changes to: region classification, income level, lending type.
-- Country reclassifications (e.g. income level changes) are historically common in WB data.

{% snapshot scd_dim_country %}

{{
    config(
        target_schema='snapshots',
        unique_key='country_iso2',
        strategy='check',
        check_cols=['region_id', 'income_level_id', 'lending_type', 'country_name'],
        invalidate_hard_deletes=True
    )
}}

select
    country_iso2,
    country_iso3,
    country_name,
    capital_city,
    region_id,
    region_name,
    income_level_id,
    income_level_name,
    lending_type,
    longitude,
    latitude,
    current_timestamp() as record_loaded_at

from {{ ref('stg_wb_countries') }}

{% endsnapshot %}
