{{
  config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='merge_key',
    partition_by={
      "field": "partition_date",
      "data_type": "date"
    },
    tags=['delta_load', 'iceberg', 'parking', 'incremental']
  )
}}

{#
  DELTA LOAD IMPLEMENTATION USING ICEBERG MERGE
  This model showcases sophisticated incremental loading with:
  - Iceberg MERGE operations for upserts
  - Date-based partitioning for query optimization
  - State management for incremental processing
  - Data quality validation
#}

with delta_source as (
  -- Read the delta load data from the seed file
  select
    -- Primary merge key (composite of location + timestamp)
    location || '_' || date_format(parse_datetime(timestamp, 'yyyy-MM-dd''T''HH:mm:ss.SSSSSSZ'), 'yyyyMMdd_HHmm') as merge_key,

    -- Core parking data
    date,
    time,
    location,
    try_cast(latitude as double) as latitude,
    try_cast(longitude as double) as longitude,
    try_cast(available_spaces as integer) as available_spaces,
    parse_datetime(timestamp, 'yyyy-MM-dd''T''HH:mm:ss.SSSSSSZ') as recorded_timestamp,

    -- Enhanced metadata
    data_source,
    ingestion_timestamp,
    pipeline_run_id,
    parse_datetime(ingestion_timestamp, 'yyyy-MM-dd''T''HH:mm:ss.SSSSSSZ') as load_timestamp,

    -- Delta load specific fields
    _load_timestamp,
    _is_incremental,
    _last_load_timestamp,

    -- Partition column for Iceberg optimization
    date(parse_datetime(timestamp, 'yyyy-MM-dd''T''HH:mm:ss.SSSSSSZ')) as partition_date,

    -- Audit columns
    current_timestamp as _dbt_loaded_at,
    'delta_load' as _load_type,
    '{{ invocation_id }}' as _dbt_invocation_id

  from {{ source('stavanger_parking', 'delta_parking_data') }}
),

validated_data as (
  -- Data quality validation and enrichment
  select
    *,
    -- Data quality checks
    case
      when recorded_timestamp is null then 0
      when location is null or location = '' then 0
      when available_spaces < 0 then 0
      when latitude < 50 or latitude > 70 then 0  -- Norway latitude bounds
      when longitude < 0 or longitude > 20 then 0  -- Norway longitude bounds
      else 1
    end as data_quality_score,

    -- Business logic enrichment
    case
      when lower(location) like '%jernbanen%' then 400
      when lower(location) like '%forum%' then 350
      when lower(location) like '%sentrum%' then 350
      when lower(location) like '%brogaten%' then 300
      when lower(location) like '%våland%' then 250
      when lower(location) like '%havneringen%' then 200
      else 200  -- Default capacity
    end as estimated_total_capacity,

    -- Derived metrics
    greatest(0, estimated_total_capacity - available_spaces) as estimated_occupancy,
    round(
      (greatest(0, estimated_total_capacity - available_spaces) * 100.0) /
      nullif(estimated_total_capacity, 0),
      2
    ) as estimated_utilization_rate

  from delta_source
),

final as (
  select
    -- Primary key and merge key
    merge_key,

    -- Core data
    date,
    time,
    location,
    latitude,
    longitude,
    available_spaces,
    recorded_timestamp,

    -- Enhanced metadata
    data_source,
    ingestion_timestamp,
    pipeline_run_id,
    load_timestamp,

    -- Delta load tracking
    _load_timestamp,
    _is_incremental,
    _last_load_timestamp,

    -- Data quality
    data_quality_score,
    estimated_total_capacity,
    estimated_occupancy,
    estimated_utilization_rate,

    -- Partition and audit
    partition_date,
    _dbt_loaded_at,
    _load_type,
    _dbt_invocation_id,

    -- Additional derived fields
    extract(hour from recorded_timestamp) as recorded_hour,
    extract(day_of_week from recorded_timestamp) as recorded_day_of_week,
    extract(month from recorded_timestamp) as recorded_month,
    extract(year from recorded_timestamp) as recorded_year,

    -- Business categorizations
    case
      when extract(hour from recorded_timestamp) between 7 and 9
        or extract(hour from recorded_timestamp) between 16 and 18 then 'Peak Hours'
      when extract(hour from recorded_timestamp) between 10 and 15 then 'Business Hours'
      else 'Off Hours'
    end as time_period,

    case
      when lower(location) like '%jernbanen%' then 'Transport Hub'
      when lower(location) like '%forum%' or lower(location) like '%sentrum%' then 'City Center'
      when lower(location) like '%havneringen%' then 'Waterfront'
      else 'Residential'
    end as location_type

  from validated_data

  {% if is_incremental() %}
    -- Incremental logic: only process records newer than the last load
    where recorded_timestamp > (
      select coalesce(max(recorded_timestamp), timestamp '1970-01-01 00:00:00')
      from {{ this }}
    )
  {% endif %}
)

select * from final
