-- staging/stg_wb_indicators.sql
-- Cast types, trim strings, drop null values.
-- Null value rows are retained in staging but flagged; downstream models filter.

with source as (
    select * from {{ source('raw', 'raw_wb_indicators') }}
),

cleaned as (
    select
        trim(indicator_code)            as indicator_code,
        trim(indicator_name)            as indicator_name,
        upper(trim(country_iso2))       as country_iso2,
        trim(country_name)              as country_name,
        cast(year as int)               as year,
        cast(value as float)            as value,
        value is not null               as has_value,
        ingested_at,
        run_id

    from source
    where
        indicator_code is not null
        and country_iso2 is not null
        and year is not null
        and year between 1960 and extract(year from current_date())
)

select * from cleaned
