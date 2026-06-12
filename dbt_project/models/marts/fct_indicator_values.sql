-- marts/fct_indicator_values.sql
-- Fact table at grain: country Ã- indicator Ã- year.
-- Surrogate keys reference dim_country and dim_indicator.
-- Incremental on year to allow historical backfill without full rebuilds.

{{
    config(
        materialized='incremental',
        unique_key=['country_key', 'indicator_key', 'year'],
        incremental_strategy='merge',
        on_schema_change='fail'
    )
}}

with source as (
    select * from {{ ref('int_indicators_pivoted') }}

    {% if is_incremental() %}
    -- for daily runs, only bring in records for the last 2 years
    -- to catch late-arriving corrections from WB
    where year >= extract(year from current_date()) - 2
    {% endif %}
),

with_keys as (
    select
        s.*,
        c.country_key,
        i.indicator_key

    from source s
    left join {{ ref('dim_country') }} c
        on s.country_iso2 = c.country_iso2
    left join {{ ref('dim_indicator') }} i
        on s.indicator_code = i.indicator_code
),

final as (
    select
        {{ generate_surrogate_key(['country_key', 'indicator_key', 'year']) }}  as fact_key,
        country_key,
        indicator_key,
        country_iso2,
        indicator_code,
        year,
        value,
        region_id,
        region_name,
        income_level_id,
        ingested_at,
        run_id

    from with_keys
    where country_key is not null
      and indicator_key is not null
)

select * from final
