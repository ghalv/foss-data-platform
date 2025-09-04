{{
  config(
    materialized='table',
    schema='analytics',
    tags=['gold', 'analytics', 'predictive', 'machine_learning', 'features']
  )
}}

{#
  GOLD LAYER - PREDICTIVE ANALYTICS FEATURES
  ============================================
  Purpose: Feature engineering for predictive modeling and ML
  Principles:
  - Feature-rich dataset for ML models
  - Time series patterns
  - Predictive indicators
  - Anomaly detection features
#}

with occupancy_facts as (
  select * from {{ ref('slv_parking_occupancy_facts') }}
),

locations as (
  select * from {{ ref('slv_parking_locations') }}
),

-- Historical patterns (last 30 days)
historical_patterns as (
  select
    f.location_key,
    f.recorded_date,
    f.recorded_hour,

    -- Basic utilization metrics
    round(avg(f.utilization_percentage), 2) as avg_utilization,
    round(max(f.utilization_percentage), 2) as max_utilization,
    round(min(f.utilization_percentage), 2) as min_utilization,
    round(stddev(f.utilization_percentage), 2) as std_utilization,

    -- Time-based patterns
    count(*) as total_readings,
    sum(case when f.is_peak_hour then 1 else 0 end) as peak_hour_readings,
    round(avg(case when f.is_peak_hour then f.utilization_percentage end), 2) as peak_hour_avg,
    round(avg(case when not f.is_peak_hour then f.utilization_percentage end), 2) as off_peak_avg,

    -- Day-of-week patterns
    round(avg(case when f.day_of_week = 1 then f.utilization_percentage end), 2) as monday_avg,
    round(avg(case when f.day_of_week = 2 then f.utilization_percentage end), 2) as tuesday_avg,
    round(avg(case when f.day_of_week = 3 then f.utilization_percentage end), 2) as wednesday_avg,
    round(avg(case when f.day_of_week = 4 then f.utilization_percentage end), 2) as thursday_avg,
    round(avg(case when f.day_of_week = 5 then f.utilization_percentage end), 2) as friday_avg,
    round(avg(case when f.day_of_week = 6 then f.utilization_percentage end), 2) as saturday_avg,
    round(avg(case when f.day_of_week = 7 then f.utilization_percentage end), 2) as sunday_avg

  from occupancy_facts f
  where f.recorded_timestamp >= current_date - interval '30' day
  group by f.location_key, f.recorded_date, f.recorded_hour
),

-- Trend features (rolling averages and changes)
trend_features as (
  select
    location_key,
    recorded_date,
    recorded_hour,
    avg_utilization,

    -- 7-day rolling average
    avg(avg_utilization) over (
      partition by location_key, recorded_hour
      order by recorded_date
      rows between 6 preceding and current row
    ) as rolling_7day_avg,

    -- Day-over-day change
    avg_utilization - lag(avg_utilization) over (
      partition by location_key, recorded_hour
      order by recorded_date
    ) as day_over_day_change,

    -- Week-over-week change
    avg_utilization - lag(avg_utilization, 7) over (
      partition by location_key, recorded_hour
      order by recorded_date
    ) as week_over_week_change,

    -- Utilization trend direction
    case
      when avg_utilization > lag(avg_utilization) over (
        partition by location_key, recorded_hour
        order by recorded_date
      ) then 'increasing'
      when avg_utilization < lag(avg_utilization) over (
        partition by location_key, recorded_hour
        order by recorded_date
      ) then 'decreasing'
      else 'stable'
    end as trend_direction

  from historical_patterns
),

-- Predictive features dataset
predictive_features as (
  select
    -- Primary keys
    hp.location_key,
    l.location_name,
    l.location_category,
    l.business_segment,
    l.geographic_zone,
    hp.recorded_date,
    hp.recorded_hour,

    -- Target variable (next hour utilization)
    lead(hp.avg_utilization) over (
      partition by hp.location_key
      order by hp.recorded_date, hp.recorded_hour
    ) as target_next_hour_utilization,

    -- Historical features
    hp.avg_utilization as current_utilization,
    hp.max_utilization,
    hp.min_utilization,
    hp.std_utilization,
    hp.peak_hour_avg,
    hp.off_peak_avg,

    -- Day-of-week features
    hp.monday_avg,
    hp.tuesday_avg,
    hp.wednesday_avg,
    hp.thursday_avg,
    hp.friday_avg,
    hp.saturday_avg,
    hp.sunday_avg,

    -- Trend features
    tf.rolling_7day_avg,
    tf.day_over_day_change,
    tf.week_over_week_change,
    tf.trend_direction,

    -- Location characteristics as features
    l.estimated_capacity,
    case when l.location_category = 'transport_hub' then 1 else 0 end as is_transport_hub,
    case when l.location_category = 'city_center' then 1 else 0 end as is_city_center,
    case when l.business_segment = 'high_traffic_premium' then 1 else 0 end as is_premium_location,
    case when l.geographic_zone = 'city_center' then 1 else 0 end as is_city_zone,

    -- Time-based features
    hp.recorded_hour,
    case when hp.recorded_hour between 7 and 9 then 1 else 0 end as is_morning_rush,
    case when hp.recorded_hour between 16 and 19 then 1 else 0 end as is_evening_rush,
    case when hp.recorded_hour between 10 and 15 then 1 else 0 end as is_business_hours,
    case when hp.recorded_hour between 20 and 23 or hp.recorded_hour between 0 and 5 then 1 else 0 end as is_off_hours,

    -- Seasonal features
    extract(dayofyear from hp.recorded_date) as day_of_year,
    sin(2 * pi() * extract(dayofyear from hp.recorded_date) / 365) as seasonal_sin,
    cos(2 * pi() * extract(dayofyear from hp.recorded_date) / 365) as seasonal_cos,

    -- Anomaly detection features
    case
      when hp.avg_utilization > hp.rolling_7day_avg + (2 * hp.std_utilization) then 1
      when hp.avg_utilization < hp.rolling_7day_avg - (2 * hp.std_utilization) then 1
      else 0
    end as is_anomaly,

    -- Capacity pressure indicators
    case when hp.avg_utilization >= 90 then 1 else 0 end as high_capacity_pressure,
    case when hp.avg_utilization >= 75 then 1 else 0 end as moderate_capacity_pressure,

    -- Metadata for ML pipeline
    current_timestamp as features_generated_at,
    concat('parking_', hp.location_key, '_', hp.recorded_date, '_', hp.recorded_hour) as prediction_id,
    'gold_analytics' as _layer,
    'predictive_features' as _feature_type,
    'stavanger_parking' as _source_system

  from historical_patterns hp
  join locations l on hp.location_key = l.location_key
  left join trend_features tf
    on hp.location_key = tf.location_key
    and hp.recorded_date = tf.recorded_date
    and hp.recorded_hour = tf.recorded_hour
  where hp.total_readings >= 3  -- Minimum data quality threshold
),

-- Final dataset with data quality filters
final_features as (
  select *
  from predictive_features
  where target_next_hour_utilization is not null  -- Only include records with prediction targets
    and current_utilization is not null
    and rolling_7day_avg is not null
  order by location_key, recorded_date desc, recorded_hour desc
)

select * from final_features
