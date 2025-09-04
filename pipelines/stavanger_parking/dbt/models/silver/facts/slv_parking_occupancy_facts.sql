{{
  config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['occupancy_key'],
    partition_by={
      "field": "recorded_date",
      "data_type": "date"
    },
    schema='analytics_staging',
    tags=['silver', 'facts', 'parking', 'occupancy', 'incremental']
  )
}}

{#
  SILVER LAYER - PARKING OCCUPANCY FACTS
  ========================================
  Purpose: Clean, validated parking occupancy measurements
  Principles:
  - Atomic transaction-level facts
  - Referential integrity with dimensions
  - Business rule validation
  - Slowly changing fact support
#}

with bronze_data as (
  select * from {{ ref('brz_raw_parking_data') }}
),

locations as (
  select * from {{ ref('slv_parking_locations') }}
),

-- Enrich and validate occupancy facts
enriched_facts as (
  select
    -- Generate composite business key
    md5(concat(
      coalesce(lower(trim(b.location)), ''),
      '_',
      coalesce(cast(b.recorded_timestamp as varchar), ''),
      '_',
      coalesce(cast(b.available_spaces_int as varchar), '')
    )) as occupancy_key,

    -- Foreign keys to dimensions
    l.location_key,
    b.merge_key as source_merge_key,

    -- Core facts
    b.recorded_timestamp,
    date(b.recorded_timestamp) as recorded_date,
    hour(b.recorded_timestamp) as recorded_hour,
    minute(b.recorded_timestamp) as recorded_minute,
    extract(dow from b.recorded_timestamp) as day_of_week,
    extract(month from b.recorded_timestamp) as month_of_year,
    extract(year from b.recorded_timestamp) as year,

    -- Occupancy measurements
    b.available_spaces_int as available_spaces,
    l.estimated_capacity as total_capacity,
    greatest(0, l.estimated_capacity - b.available_spaces_int) as occupied_spaces,

    -- Utilization calculations
    case
      when l.estimated_capacity > 0 then
        round((greatest(0, l.estimated_capacity - b.available_spaces_int) * 100.0) / l.estimated_capacity, 2)
      else null
    end as utilization_percentage,

    -- Business categorizations
    case
      when hour(b.recorded_timestamp) between 7 and 9 or hour(b.recorded_timestamp) between 16 and 19 then true
      else false
    end as is_peak_hour,

    case
      when hour(b.recorded_timestamp) between 6 and 9 then 'morning_rush'
      when hour(b.recorded_timestamp) between 16 and 19 then 'evening_rush'
      when hour(b.recorded_timestamp) between 10 and 15 then 'business_hours'
      when hour(b.recorded_timestamp) between 20 and 23 or hour(b.recorded_timestamp) between 0 and 5 then 'off_hours'
      else 'other'
    end as time_period,

    -- Geographic context
    b.latitude_double as latitude,
    b.longitude_double as longitude,
    l.geographic_zone,
    l.location_category,

    -- Quality and validation
    case
      when b.available_spaces_int < 0 then 'negative_spaces'
      when b.available_spaces_int > l.estimated_capacity then 'over_capacity'
      when b.available_spaces_int is null then 'missing_data'
      else 'valid'
    end as data_quality_flag,

    -- Business rules validation
    case
      when utilization_percentage >= 100 then 'at_capacity'
      when utilization_percentage >= 90 then 'near_capacity'
      when utilization_percentage >= 75 then 'high_utilization'
      when utilization_percentage >= 50 then 'moderate_utilization'
      when utilization_percentage >= 25 then 'low_utilization'
      else 'very_low_utilization'
    end as utilization_category,

    -- Derived business metrics
    case
      when is_peak_hour and utilization_percentage >= 85 then 'peak_constraint'
      when is_peak_hour and utilization_percentage < 85 then 'peak_available'
      when not is_peak_hour and utilization_percentage >= 60 then 'off_peak_efficient'
      else 'off_peak_available'
    end as operational_status,

    -- Metadata
    b.pipeline_run_id,
    b._bronze_loaded_at,
    current_timestamp as _silver_loaded_at,
    'silver_fact' as _layer,
    'stavanger_parking' as _source_system

  from bronze_data b
  left join locations l
    on md5(lower(trim(b.location))) = l.location_key
  where b.has_valid_timestamp = 1
    and b.has_valid_spaces = 1
),

-- Quality gate: Only valid measurements
quality_filtered as (
  select *
  from enriched_facts
  where data_quality_flag = 'valid'
    and utilization_percentage is not null
    and utilization_percentage between 0 and 150  -- Allow some over-capacity
)

select * from quality_filtered
