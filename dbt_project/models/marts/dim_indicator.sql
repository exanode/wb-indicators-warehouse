-- marts/dim_indicator.sql
-- One row per indicator code with surrogate key.
-- Name is taken from the most recently ingested record for that code.

with latest as (
    select
        indicator_code,
        indicator_name,
        row_number() over (
            partition by indicator_code
            order by ingested_at desc
        ) as rn
    from {{ ref('stg_wb_indicators') }}
),

deduped as (
    select indicator_code, indicator_name
    from latest
    where rn = 1
),

final as (
    select
        {{ generate_surrogate_key(['indicator_code']) }}    as indicator_key,
        indicator_code,
        indicator_name,
        current_timestamp()                                  as dbt_created_at

    from deduped
)

select * from final
