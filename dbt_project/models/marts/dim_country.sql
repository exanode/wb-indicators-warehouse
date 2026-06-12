-- marts/dim_country.sql
-- Kimball-style country dimension with surrogate key.
-- SCD Type 2 history is tracked in the snapshot; this is the current view.

with base as (
    select * from {{ ref('stg_wb_countries') }}
),

final as (
    select
        {{ generate_surrogate_key(['country_iso2']) }}   as country_key,
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
        ingested_at                                      as dbt_created_at

    from base
)

select * from final
