

with daily_metrics as (
    select * from "memory"."default_intermediate"."int_daily_parking_metrics"
),

dim_locations as (
    select * from "memory"."default_marts_core"."dim_parking_locations"
),

parking_insights as (
    select
        -- Date and location dimensions
        daily_metrics.recorded_date,
        daily_metrics.parking_location,
        daily_metrics.parking_type,
        daily_metrics.parking_zone,
        
        -- Location attributes
        dim_locations.location_category,
        dim_locations.capacity_category,
        dim_locations.pricing_tier,
        
        -- Key performance indicators
        daily_metrics.avg_utilization_rate_rounded as daily_avg_utilization,
        daily_metrics.max_utilization_rate as daily_peak_utilization,
        daily_metrics.peak_hour_percentage,
        daily_metrics.critical_status_percentage,
        
        -- Capacity analysis
        daily_metrics.avg_capacity,
        daily_metrics.avg_occupancy,
        round((daily_metrics.avg_occupancy / daily_metrics.avg_capacity) * 100, 2) as effective_utilization,
        
        -- Time-based insights
        daily_metrics.morning_rush_readings,
        daily_metrics.evening_rush_readings,
        daily_metrics.business_hours_readings,
        daily_metrics.off_hours_readings,
        
        -- Revenue insights
        daily_metrics.avg_price_per_hour,
        round((daily_metrics.avg_occupancy * daily_metrics.avg_price_per_hour * 24), 2) as estimated_daily_revenue,
        
        -- Business intelligence
        case 
            when daily_metrics.avg_utilization_rate_rounded >= 80 then 'High Demand - Consider Expansion'
            when daily_metrics.avg_utilization_rate_rounded >= 60 then 'Moderate Demand - Monitor Trends'
            when daily_metrics.avg_utilization_rate_rounded >= 40 then 'Low Demand - Marketing Opportunity'
            else 'Very Low Demand - Strategic Review Needed'
        end as business_recommendation,
        
        case 
            when daily_metrics.peak_hour_percentage >= 30 then 'Peak Hour Dominant'
            when daily_metrics.peak_hour_percentage >= 20 then 'Moderate Peak Usage'
            else 'Even Distribution'
        end as usage_pattern,
        
        case 
            when daily_metrics.critical_status_percentage >= 20 then 'Frequent Capacity Issues'
            when daily_metrics.critical_status_percentage >= 10 then 'Occasional Capacity Issues'
            else 'Stable Capacity'
        end as capacity_health,
        
        -- Metadata
        current_timestamp as _loaded_at,
        'marketing' as _model_type
        
    from daily_metrics
    left join dim_locations 
        on daily_metrics.parking_location = dim_locations.location_name
        and daily_metrics.parking_type = dim_locations.parking_type
        and daily_metrics.parking_zone = dim_locations.parking_zone
),

final as (
    select
        *,
        -- Additional derived insights
        case 
            when location_category = 'Indoor' and daily_avg_utilization >= 70 then 'Premium Indoor - High Value'
            when location_category = 'Indoor' and daily_avg_utilization < 70 then 'Premium Indoor - Growth Potential'
            when location_category = 'Outdoor' and daily_avg_utilization >= 60 then 'Outdoor - Good Performance'
            when location_category = 'Outdoor' and daily_avg_utilization < 60 then 'Outdoor - Development Opportunity'
            when location_category = 'Street' and daily_avg_utilization >= 50 then 'Street - Adequate Usage'
            else 'Street - Optimization Needed'
        end as location_strategy,
        
        -- Revenue optimization score
        round(
            (daily_avg_utilization / 100) * 
            (peak_hour_percentage / 100) * 
            (case when pricing_tier = 'Premium' then 1.2 when pricing_tier = 'Standard' then 1.0 else 0.8 end),
            3
        ) as revenue_optimization_score
        
    from parking_insights
)

select * from final