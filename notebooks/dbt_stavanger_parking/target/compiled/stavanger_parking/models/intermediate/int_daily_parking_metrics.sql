

with staging as (
    select * from "memory"."default_staging"."stg_parking_data"
),

daily_metrics as (
    select
        recorded_date,
        parking_location,
        parking_type,
        parking_zone,
        
        -- Count metrics
        count(*) as total_readings,
        count(distinct parking_record_id) as unique_records,
        
        -- Capacity metrics
        avg(total_capacity) as avg_capacity,
        max(total_capacity) as max_capacity,
        min(total_capacity) as min_capacity,
        
        -- Occupancy metrics
        avg(current_occupancy) as avg_occupancy,
        max(current_occupancy) as max_occupancy,
        min(current_occupancy) as min_occupancy,
        avg(utilization_rate) as avg_utilization_rate,
        max(utilization_rate) as max_utilization_rate,
        min(utilization_rate) as min_utilization_rate,
        
        -- Peak hour analysis
        sum(case when is_peak_hour = 1 then 1 else 0 end) as peak_hour_readings,
        avg(case when is_peak_hour = 1 then utilization_rate else null end) as peak_hour_avg_utilization,
        
        -- Time period analysis
        sum(case when time_period = 'Morning Rush' then 1 else 0 end) as morning_rush_readings,
        sum(case when time_period = 'Evening Rush' then 1 else 0 end) as evening_rush_readings,
        sum(case when time_period = 'Business Hours' then 1 else 0 end) as business_hours_readings,
        sum(case when time_period = 'Off Hours' then 1 else 0 end) as off_hours_readings,
        
        -- Pricing metrics
        avg(price_per_hour) as avg_price_per_hour,
        max(price_per_hour) as max_price_per_hour,
        min(price_per_hour) as min_price_per_hour,
        
        -- Status distribution
        sum(case when occupancy_status = 'Critical' then 1 else 0 end) as critical_status_count,
        sum(case when occupancy_status = 'High' then 1 else 0 end) as high_status_count,
        sum(case when occupancy_status = 'Medium' then 1 else 0 end) as medium_status_count,
        sum(case when occupancy_status = 'Low' then 1 else 0 end) as low_status_count,
        sum(case when occupancy_status = 'Very Low' then 1 else 0 end) as very_low_status_count
        
    from staging
    group by 1, 2, 3, 4
),

final as (
    select
        *,
        -- Derived metrics
        round(peak_hour_avg_utilization, 2) as peak_hour_avg_utilization_rounded,
        round(avg_utilization_rate, 2) as avg_utilization_rate_rounded,
        
        -- Peak hour percentage
        case 
            when total_readings > 0 then round((CAST(peak_hour_readings AS DOUBLE) / total_readings) * 100, 2)
            else 0 
        end as peak_hour_percentage,
        
        -- Critical status percentage
        case 
            when total_readings > 0 then round((CAST(critical_status_count AS DOUBLE) / total_readings) * 100, 2)
            else 0 
        end as critical_status_percentage,
        
        -- Metadata
        current_timestamp as _loaded_at,
        'intermediate' as _model_type
        
    from daily_metrics
)

select * from final