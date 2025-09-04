{{
  config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['merge_key'],
    partition_by={
      "field": "recorded_date",
      "data_type": "date"
    },
    schema='analytics_staging',
    tags=['bronze', 'landing', 'raw', 'parking', 'iceberg', 'incremental']
  )
}}

{#
  BRONZE LAYER - LANDING ZONE
  ============================
  Purpose: Store raw data as-is from source with minimal transformation
  Principles:
  - No business logic
  - Minimal data type casting only
  - Preserve source data integrity
  - Enable time travel and audit capabilities
  - Support incremental loading with merge
#}

with source_data as (
  -- Raw source data from delta load
  select * from {{ source('stavanger_parking', 'delta_parking_data') }}
),

bronze_landing as (
  select
    -- Primary merge key for incremental loading
    merge_key,

    -- Raw source fields (preserved as-is)
    location,
    latitude,
    longitude,
    available_spaces,
    timestamp,
    date,
    time,

    -- Minimal type casting for partitioning and basic validation
    try_cast(timestamp as timestamp) as recorded_timestamp,
    date(try_cast(timestamp as timestamp)) as recorded_date,
    try_cast(available_spaces as integer) as available_spaces_int,
    try_cast(latitude as double) as latitude_double,
    try_cast(longitude as double) as longitude_double,

    -- Data quality indicators (minimal validation)
    case
      when timestamp is not null and try_cast(timestamp as timestamp) is not null then 1
      else 0
    end as has_valid_timestamp,

    case
      when available_spaces is not null and try_cast(available_spaces as integer) is not null then 1
      else 0
    end as has_valid_spaces,

    case
      when latitude is not null and try_cast(latitude as double) is not null
           and longitude is not null and try_cast(longitude as double) is not null then 1
      else 0
    end as has_valid_coordinates,

    -- Metadata for audit trail
    {{ var('pipeline_run_id', 'unknown') }} as pipeline_run_id,
    current_timestamp as _bronze_loaded_at,
    'bronze_landing' as _layer,
    'stavanger_parking' as _source_system

  from source_data
),

-- Quality gate: Only accept records with minimum required fields
quality_filtered as (
  select *
  from bronze_landing
  where has_valid_timestamp = 1
    and has_valid_spaces = 1
    and location is not null
)

select * from quality_filtered
