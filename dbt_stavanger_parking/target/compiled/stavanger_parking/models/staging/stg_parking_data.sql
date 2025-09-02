

with source as (
    -- Live seed from ingestion
    select * from memory.default_raw_data.live_parking
),

staged as (
    select
        -- Primary key (synthetic as live seed lacks id)
        row_number() over (order by fetched_at, name) as parking_record_id,

        -- Timestamps
        try_cast(fetched_at as timestamp) as recorded_at,
        date(try_cast(fetched_at as timestamp)) as recorded_date,
        extract(hour from try_cast(fetched_at as timestamp)) as recorded_hour,
        extract(dow from try_cast(fetched_at as timestamp)) as recorded_day_of_week,
        extract(month from try_cast(fetched_at as timestamp)) as recorded_month,
        extract(year from try_cast(fetched_at as timestamp)) as recorded_year,

        -- Location information
        name as parking_location,
        cast(null as varchar) as parking_type,
        cast(null as varchar) as parking_zone,

        -- Capacity and occupancy (capacity unknown; we only have available)
        cast(null as integer) as total_capacity,
        cast(null as integer) as current_occupancy,
        try_cast(available_spaces as integer) as available_spaces,
        cast(null as double) as utilization_rate,

        -- Pricing (unknown)
        cast(null as double) as price_per_hour,

        -- Business logic
        cast(null as integer) as is_peak_hour,

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