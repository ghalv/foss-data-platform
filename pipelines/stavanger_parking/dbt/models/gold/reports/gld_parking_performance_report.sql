{{
  config(
    materialized='table',
    schema='analytics',
    tags=['gold', 'reports', 'parking', 'performance', 'business_intelligence']
  )
}}

{#
  GOLD LAYER - PARKING PERFORMANCE REPORT
  ========================================
  Purpose: Business-ready performance analytics for reporting
  Principles:
  - Aggregated business metrics
  - Executive-level insights
  - Performance KPIs
  - Trend analysis ready
#}

with occupancy_facts as (
  select * from {{ ref('slv_parking_occupancy_facts') }}
),

locations as (
  select * from {{ ref('slv_parking_locations') }}
),

date_dim as (
  select * from {{ ref('slv_date_dimension') }}
),

-- Daily location performance
daily_performance as (
  select
    f.recorded_date,
    f.location_key,
    l.location_name,
    l.location_category,
    l.business_segment,
    l.geographic_zone,

    -- Volume metrics
    count(*) as total_readings,
    count(distinct concat(cast(f.recorded_hour as varchar), ':', cast(f.recorded_minute as varchar))) as unique_time_slots,

    -- Occupancy metrics
    round(avg(f.available_spaces), 1) as avg_available_spaces,
    round(avg(f.occupied_spaces), 1) as avg_occupied_spaces,
    round(avg(f.utilization_percentage), 2) as avg_utilization_pct,
    round(max(f.utilization_percentage), 2) as peak_utilization_pct,
    round(min(f.utilization_percentage), 2) as min_utilization_pct,

    -- Peak hour analysis
    sum(case when f.is_peak_hour then 1 else 0 end) as peak_hour_readings,
    round(avg(case when f.is_peak_hour then f.utilization_percentage end), 2) as peak_hour_avg_utilization,
    round(max(case when f.is_peak_hour then f.utilization_percentage end), 2) as peak_hour_max_utilization,

    -- Time period distribution
    sum(case when f.time_period = 'morning_rush' then 1 else 0 end) as morning_rush_count,
    sum(case when f.time_period = 'evening_rush' then 1 else 0 end) as evening_rush_count,
    sum(case when f.time_period = 'business_hours' then 1 else 0 end) as business_hours_count,
    sum(case when f.time_period = 'off_hours' then 1 else 0 end) as off_hours_count,

    -- Utilization categories
    sum(case when f.utilization_category = 'at_capacity' then 1 else 0 end) as at_capacity_count,
    sum(case when f.utilization_category = 'near_capacity' then 1 else 0 end) as near_capacity_count,
    sum(case when f.utilization_category = 'high_utilization' then 1 else 0 end) as high_utilization_count,

    -- Operational status
    sum(case when f.operational_status = 'peak_constraint' then 1 else 0 end) as peak_constraint_count,
    sum(case when f.operational_status = 'peak_available' then 1 else 0 end) as peak_available_count

  from occupancy_facts f
  join locations l on f.location_key = l.location_key
  group by 1, 2, 3, 4, 5, 6
),

-- Business intelligence calculations
business_insights as (
  select
    *,

    -- Utilization KPIs
    case
      when avg_utilization_pct >= 90 then 'Critical - At Capacity'
      when avg_utilization_pct >= 75 then 'High - Near Capacity'
      when avg_utilization_pct >= 50 then 'Moderate - Good Utilization'
      when avg_utilization_pct >= 25 then 'Low - Underutilized'
      else 'Very Low - Significant Opportunity'
    end as utilization_status,

    -- Peak efficiency score
    case
      when peak_hour_avg_utilization >= 85 then 'Excellent Peak Performance'
      when peak_hour_avg_utilization >= 70 then 'Good Peak Performance'
      when peak_hour_avg_utilization >= 50 then 'Moderate Peak Performance'
      else 'Poor Peak Performance'
    end as peak_efficiency_rating,

    -- Revenue optimization potential
    case
      when business_segment = 'high_traffic_premium' and avg_utilization_pct < 80 then 'High Revenue Opportunity'
      when business_segment = 'urban_premium' and avg_utilization_pct < 70 then 'Medium Revenue Opportunity'
      when location_category = 'transport_hub' and peak_hour_avg_utilization < 75 then 'Peak Revenue Opportunity'
      else 'Optimal Revenue Performance'
    end as revenue_optimization_opportunity,

    -- Operational recommendations
    case
      when at_capacity_count > total_readings * 0.3 then 'Consider Capacity Expansion'
      when peak_constraint_count > total_readings * 0.2 then 'Address Peak Hour Constraints'
      when avg_utilization_pct < 30 and business_segment like '%premium%' then 'Marketing Opportunity'
      else 'Monitor Performance'
    end as operational_recommendation,

    -- Performance score (0-100)
    round(
      (avg_utilization_pct * 0.4) +
      (least(peak_hour_avg_utilization, 100) * 0.3) +
      ((total_readings / 96.0) * 100 * 0.3),  -- Coverage score (96 = 15min intervals per day)
      1
    ) as overall_performance_score

  from daily_performance
),

-- Final report with metadata
final_report as (
  select
    *,
    current_timestamp as report_generated_at,
    'gold_report' as _layer,
    'business_intelligence' as _report_type,
    'stavanger_parking' as _source_system
  from business_insights
  order by recorded_date desc, overall_performance_score desc
)

select * from final_report
