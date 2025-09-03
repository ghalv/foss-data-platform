
  
    

    create table "iceberg"."analytics_marts_core"."fct_parking_utilization__dbt_tmp"
      
      
    as (
      

with staging as (
    select * from "iceberg"."analytics_staging"."stg_parking_data"
),

dim_locations as (
    select * from "iceberg"."analytics_marts_core"."dim_parking_locations"
),

fact_table as (
    select
        -- Fact table primary key
        staging.parking_record_id as fact_key,
        
        -- Foreign keys
        dim_locations.location_key,
        
        -- Date and time dimensions
        staging.recorded_date as date_key,
        staging.recorded_hour as hour_key,
        staging.recorded_day_of_week as day_of_week_key,
        staging.recorded_month as month_key,
        staging.recorded_year as year_key,
        
        -- Measures (facts)
        staging.current_occupancy as occupancy_count,
        staging.available_spaces as available_spaces_count,
        staging.utilization_rate as utilization_percentage,
        staging.price_per_hour as hourly_rate,
        
        -- Binary indicators
        staging.is_peak_hour as peak_hour_indicator,
        
        -- Categorical measures
        staging.occupancy_status,
        staging.time_period,
        
        -- Calculated measures
        case 
            when staging.is_peak_hour = 1 then staging.utilization_rate
            else null 
        end as peak_hour_utilization,
        
        case 
            when staging.is_peak_hour = 0 then staging.utilization_rate
            else null 
        end as off_peak_utilization,
        
        -- Revenue potential (occupancy * price)
        round((staging.current_occupancy * staging.price_per_hour) / 24, 2) as daily_revenue_potential,
        
        -- Metadata
        staging.recorded_at as source_timestamp,
        current_timestamp as _loaded_at,
        'fact' as _model_type
        
    from staging
    left join dim_locations 
        on staging.parking_location = dim_locations.location_name
        and staging.parking_type = dim_locations.parking_type
        and staging.parking_zone = dim_locations.parking_zone
),

final as (
    select
        *,
        -- Additional business metrics
        case 
            when utilization_percentage >= 90 then 'Critical Capacity'
            when utilization_percentage >= 75 then 'High Demand'
            when utilization_percentage >= 50 then 'Moderate Usage'
            when utilization_percentage >= 25 then 'Low Usage'
            else 'Minimal Usage'
        end as business_impact_level,
        
        -- Time efficiency metric
        case 
            when peak_hour_indicator = 1 and utilization_percentage >= 75 then 'Peak Efficiency'
            when peak_hour_indicator = 1 and utilization_percentage < 75 then 'Peak Underutilization'
            when peak_hour_indicator = 0 and utilization_percentage >= 50 then 'Off-Peak Efficiency'
            else 'Off-Peak Underutilization'
        end as efficiency_status
        
    from fact_table
)

select * from final
    );

  