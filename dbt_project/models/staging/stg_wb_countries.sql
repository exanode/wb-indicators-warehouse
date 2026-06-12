-- staging/stg_wb_countries.sql
-- Rename and clean country metadata from WB API.
-- Excludes aggregate regions (e.g. "World", "High income") which have no iso3.

with source as (
    select * from {{ source('raw', 'raw_wb_countries') }}
),

cleaned as (
    select
        upper(trim(country_iso2))           as country_iso2,
        trim(country_iso3)                  as country_iso3,
        trim(country_name)                  as country_name,
        nullif(trim(capital_city), '')      as capital_city,
        trim(region_id)                     as region_id,
        trim(region_name)                   as region_name,
        trim(income_level_id)               as income_level_id,
        trim(income_level_name)             as income_level_name,
        trim(lending_type)                  as lending_type,
        cast(longitude as float)            as longitude,
        cast(latitude as float)             as latitude,
        ingested_at

    from source
    where
        country_iso2 is not null
        -- WB returns aggregate regions (World, South Asia, etc.) alongside countries.
        -- Aggregates have no iso3 code; filter them here so dims only contain real countries.
        and nullif(trim(country_iso3), '') is not null
)

select * from cleaned
