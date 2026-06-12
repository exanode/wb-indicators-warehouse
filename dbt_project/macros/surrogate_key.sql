-- macros/surrogate_key.sql
-- MD5-based surrogate key across composite fields.
-- Null-safe: coalesces each field to empty string before concatenation.

{% macro generate_surrogate_key(field_list) %}
    md5(
        {%- for field in field_list %}
        coalesce(cast({{ field }} as varchar), '')
        {%- if not loop.last %} || '|' || {% endif %}
        {%- endfor %}
    )
{% endmacro %}
