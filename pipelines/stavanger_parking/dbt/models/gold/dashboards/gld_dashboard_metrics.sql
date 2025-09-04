{{
  config(
    materialized='view',
    schema='analytics',
    tags=['gold', 'dashboards', 'metrics', 'real_time', 'kpi']
  )
}}

{#
  GOLD LAYER - DASHBOARD METRICS
  ================================
  Purpose: Real-time dashboard KPIs and metrics
  Principles:
  - Optimized for dashboard performance
  - Pre-aggregated for speed
  - Current state focus
  - KPI-ready format
#}

with current_occupancy as (
  -- Get latest reading for each location (within last 30 minutes)
  select
    f.location_key,
    f.recorded_timestamp,
    f.available_spaces,
    f.occupied_spaces,
    f.utilization_percentage,
    f.operational_status,
    row_number() over (
      partition by f.location_key
      order by f.recorded_timestamp desc
    ) as recency_rank
  from {{ ref('slv_parking_occupancy_facts') }} f
  where f.recorded_timestamp >= current_timestamp - interval '30' minute
),

latest_readings as (
  select *
  from current_occupancy
  where recency_rank = 1
),

location_summary as (
  select
    l.location_name,
    l.location_category,
    l.business_segment,
    l.geographic_zone,
    l.estimated_capacity,
    lr.recorded_timestamp as last_updated,
    lr.available_spaces,
    lr.occupied_spaces,
    lr.utilization_percentage,
    lr.operational_status,

    -- Time since last update
    extract(epoch from (current_timestamp - lr.recorded_timestamp)) / 60 as minutes_since_update,

    -- Status indicators
    case
      when lr.recorded_timestamp >= current_timestamp - interval '10' minute then 'current'
      when lr.recorded_timestamp >= current_timestamp - interval '30' minute then 'recent'
      else 'stale'
    end as data_freshness,

    -- Capacity status
    case
      when lr.utilization_percentage >= 95 then 'full'
      when lr.utilization_percentage >= 85 then 'almost_full'
      when lr.utilization_percentage >= 70 then 'busy'
      when lr.utilization_percentage >= 40 then 'moderate'
      else 'available'
    end as capacity_status

  from {{ ref('slv_parking_locations') }} l
  left join latest_readings lr on l.location_key = lr.location_key
),

-- System-wide KPIs
system_kpis as (
  select
    count(*) as total_locations,
    count(case when data_freshness = 'current' then 1 end) as current_locations,
    round(avg(utilization_percentage), 1) as system_avg_utilization,
    round(avg(estimated_capacity), 0) as system_total_capacity,
    round(sum(occupied_spaces), 0) as system_total_occupied,
    round(sum(available_spaces), 0) as system_total_available,

    -- System status
    case
      when avg(utilization_percentage) >= 90 then 'system_overloaded'
      when avg(utilization_percentage) >= 75 then 'system_busy'
      when avg(utilization_percentage) >= 50 then 'system_moderate'
      else 'system_available'
    end as system_status,

    -- Critical locations
    count(case when capacity_status = 'full' then 1 end) as critical_locations,
    count(case when capacity_status = 'almost_full' then 1 end) as near_critical_locations

  from location_summary
),

-- Peak hour analysis (last 24 hours)
peak_analysis as (
  select
    hour(recorded_timestamp) as hour_of_day,
    round(avg(utilization_percentage), 1) as avg_utilization,
    round(max(utilization_percentage), 1) as peak_utilization,
    count(*) as reading_count
  from {{ ref('slv_parking_occupancy_facts') }}
  where recorded_timestamp >= current_date - interval '1' day
    and is_peak_hour = true
  group by hour(recorded_timestamp)
),

-- Trend analysis (last 7 days)
trend_analysis as (
  select
    date(recorded_timestamp) as date_key,
    round(avg(utilization_percentage), 1) as daily_avg_utilization,
    round(max(utilization_percentage), 1) as daily_peak_utilization,
    count(distinct location_key) as active_locations,
    count(*) as total_readings
  from {{ ref('slv_parking_occupancy_facts') }}
  where recorded_timestamp >= current_date - interval '7' day
  group by date(recorded_timestamp)
  order by date_key desc
  limit 7
),

-- Final dashboard dataset
dashboard_data as (
  select
    -- Location-level metrics
    ls.location_name,
    ls.location_category,
    ls.business_segment,
    ls.geographic_zone,
    ls.estimated_capacity,
    ls.last_updated,
    ls.available_spaces,
    ls.occupied_spaces,
    ls.utilization_percentage,
    ls.operational_status,
    ls.minutes_since_update,
    ls.data_freshness,
    ls.capacity_status,

    -- System-wide KPIs (repeated for each row for easy dashboard filtering)
    sk.total_locations,
    sk.current_locations,
    sk.system_avg_utilization,
    sk.system_total_capacity,
    sk.system_total_occupied,
    sk.system_total_available,
    sk.system_status,
    sk.critical_locations,
    sk.near_critical_locations,

    -- Metadata
    current_timestamp as dashboard_updated_at,
    'gold_dashboard' as _layer,
    'real_time_metrics' as _metric_type,
    'stavanger_parking' as _source_system

  from location_summary ls
  cross join system_kpis sk
)

select * from dashboard_data
order by utilization_percentage desc, location_name
