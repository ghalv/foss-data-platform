
  create or replace view
    "memory"."default_staging"."stg_parking_data"
  security definer
  as
    

with source as (
    select * from "memory"."default_raw_data"."raw_parking_data"
),

staged as (
    select
        -- Primary key
        id as parking_record_id,
        
        -- Timestamps
        timestamp as recorded_at,
        date(timestamp) as recorded_date,
        extract(hour from timestamp) as recorded_hour,
        extract(dow from timestamp) as recorded_day_of_week,
        extract(month from timestamp) as recorded_month,
        extract(year from timestamp) as recorded_year,
        
        -- Location information
        location as parking_location,
        parking_type,
        zone as parking_zone,
        
        -- Capacity and occupancy
        capacity as total_capacity,
        occupancy as current_occupancy,
        available_spaces,
        utilization_rate,
        
        -- Pricing
        price_per_hour,
        
        -- Business logic
        is_peak_hour,
        
        -- Metadata
        current_timestamp as _loaded_at,
        'staging' as _model_type
        
    from source
),

final as (
    select
        *,
        -- Additional business logic
        case 
            when utilization_rate >= 90 then 'Critical'
            when utilization_rate >= 75 then 'High'
            when utilization_rate >= 50 then 'Medium'
            when utilization_rate >= 25 then 'Low'
            else 'Very Low'
        end as occupancy_status,
        
        -- Time-based categorizations
        case 
            when recorded_hour between 6 and 9 then 'Morning Rush'
            when recorded_hour between 16 and 19 then 'Evening Rush'
            when recorded_hour between 10 and 15 then 'Business Hours'
            else 'Off Hours'
        end as time_period
        
    from staged
)

select * from final
  ;
