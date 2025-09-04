{{
  config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['location_key'],
    schema='analytics_staging',
    tags=['silver', 'entities', 'dimension', 'parking', 'locations']
  )
}}

{#
  SILVER LAYER - PARKING LOCATIONS ENTITY
  ========================================
  Purpose: Clean, enriched parking location master data
  Principles:
  - Standardized business entities
  - Data quality validation and enrichment
  - Slowly changing dimension support
  - Business rule application
#}

with bronze_data as (
  select * from {{ ref('brz_raw_parking_data') }}
),

-- Extract unique locations with quality validation
location_master as (
  select distinct
    -- Generate stable business key
    md5(lower(trim(location))) as location_key,

    -- Standardize location attributes
    trim(location) as location_name,
    trim(lower(location)) as location_name_lower,

    -- Geographic validation and enrichment
    avg(latitude_double) as latitude,
    avg(longitude_double) as longitude,

    -- Business intelligence enrichment
    case
      when lower(location) like '%jernbanen%' then 'transport_hub'
      when lower(location) like '%forum%' then 'city_center'
      when lower(location) like '%sentrum%' then 'city_center'
      when lower(location) like '%stasjon%' then 'transport_hub'
      when lower(location) like '%park%' then 'recreational'
      else 'residential'
    end as location_category,

    case
      when lower(location) like '%jernbanen%' then 'premium'
      when lower(location) like '%forum%' then 'premium'
      when lower(location) like '%sentrum%' then 'premium'
      else 'standard'
    end as pricing_tier,

    -- Capacity estimation based on location type
    case
      when lower(location) like '%jernbanen%' then 400
      when lower(location) like '%forum%' then 350
      when lower(location) like '%sentrum%' then 350
      when lower(location) like '%park%' then 200
      else 250
    end as estimated_capacity,

    -- Location characteristics
    case
      when lower(location) like '%jernbanen%' or lower(location) like '%forum%' then 'multi_level'
      else 'surface'
    end as facility_type,

    -- Operational attributes
    true as is_active,
    'stavanger' as city,
    'norway' as country,

    -- Metadata
    count(*) as total_readings,
    min(recorded_timestamp) as first_observed_at,
    max(recorded_timestamp) as last_observed_at,

    -- Data quality score
    round(avg(has_valid_timestamp + has_valid_spaces + has_valid_coordinates) / 3.0, 2) as data_quality_score

  from bronze_data
  where has_valid_timestamp = 1
    and has_valid_spaces = 1
    and location is not null
  group by trim(location), trim(lower(location))
),

-- Apply business rules and validation
enriched_locations as (
  select
    *,

    -- Business rule validations
    case
      when latitude is null or longitude is null then false
      when latitude < 50 or latitude > 75 then false  -- Norway latitude bounds
      when longitude < 0 or longitude > 30 then false  -- Norway longitude bounds
      else true
    end as has_valid_coordinates,

    case
      when estimated_capacity < 10 or estimated_capacity > 2000 then false
      else true
    end as has_valid_capacity,

    -- Derived business attributes
    case
      when location_category = 'transport_hub' and pricing_tier = 'premium' then 'high_traffic_premium'
      when location_category = 'city_center' and pricing_tier = 'premium' then 'urban_premium'
      when location_category = 'residential' then 'neighborhood_standard'
      else 'standard'
    end as business_segment,

    -- Geographic clustering (simplified)
    case
      when latitude between 58.9 and 59.0 and longitude between 5.7 and 5.8 then 'city_center'
      else 'suburban'
    end as geographic_zone,

    -- Operational status
    case
      when last_observed_at >= current_date - interval '7' day then 'active'
      when last_observed_at >= current_date - interval '30' day then 'inactive_recent'
      else 'inactive'
    end as operational_status,

    -- Update tracking for SCD
    current_timestamp as _silver_loaded_at,
    'silver_entity' as _layer,
    'stavanger_parking' as _source_system

  from location_master
),

-- Quality gate: Only high-quality location data
quality_filtered as (
  select *
  from enriched_locations
  where data_quality_score >= 0.8
    and has_valid_coordinates = true
    and has_valid_capacity = true
)

select * from quality_filtered
