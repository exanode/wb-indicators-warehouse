-- intermediate/int_indicators_pivoted.sql
-- Join indicator values with country dimension.
-- Enforces the expected grain: country x indicator x year.

with indicators as (
    select * from {{ ref('stg_wb_indicators') }}
    where has_value = true
),

countries as (
    select
        country_iso2,
        country_name,
        region_id,
        region_name,
        income_level_id,
        income_level_name

    from {{ ref('stg_wb_countries') }}
),

joined as (
    select
        i.indicator_code,
        i.indicator_name,
        i.country_iso2,
        coalesce(c.country_name, i.country_name)    as country_name,
        c.region_id,
        c.region_name,
        c.income_level_id,
        c.income_level_name,
        i.year,
        i.value,
        i.ingested_at,
        i.run_id

    from indicators i
    left join countries c
        on i.country_iso2 = c.country_iso2
)

select * from joined
