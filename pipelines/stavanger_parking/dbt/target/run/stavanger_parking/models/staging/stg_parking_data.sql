
  
    

    create table "memory"."default_staging"."stg_parking_data"
      
      
    as (
      

with source as (
    -- Use raw_parking_data source defined in sources.yml
    select * from "memory"."default"."raw_parking_data"
),

staged as (
    select
        -- Primary key (generate from location and timestamp)
        row_number() over (order by location, timestamp) as parking_record_id,

        -- Timestamps
        try_cast(timestamp as timestamp) as recorded_at,
        date(try_cast(timestamp as timestamp)) as recorded_date,
        extract(hour from try_cast(timestamp as timestamp)) as recorded_hour,
        extract(dow from try_cast(timestamp as timestamp)) as recorded_day_of_week,
        extract(month from try_cast(timestamp as timestamp)) as recorded_month,
        extract(year from try_cast(timestamp as timestamp)) as recorded_year,

        -- Location information
        location as parking_location,
        try_cast(latitude as double) as latitude,
        try_cast(longitude as double) as longitude,
        'Unknown' as parking_type,  -- Not provided by API
        'Unknown' as parking_zone,  -- Not provided by API

        -- Capacity and occupancy (estimated from location type)
        case
            when lower(location) like '%jernbanen%' then 400
            when lower(location) like '%forum%' then 350
            when lower(location) like '%sentrum%' then 350
            else 250
        end as total_capacity,
        greatest(0, try_cast(available_spaces as integer)) as available_spaces,
        greatest(0, case
            when lower(location) like '%jernbanen%' then 400 - try_cast(available_spaces as integer)
            when lower(location) like '%forum%' then 350 - try_cast(available_spaces as integer)
            when lower(location) like '%sentrum%' then 350 - try_cast(available_spaces as integer)
            else 250 - try_cast(available_spaces as integer)
        end) as current_occupancy,
        (greatest(0, case
            when lower(location) like '%jernbanen%' then 400 - try_cast(available_spaces as integer)
            when lower(location) like '%forum%' then 350 - try_cast(available_spaces as integer)
            when lower(location) like '%sentrum%' then 350 - try_cast(available_spaces as integer)
            else 250 - try_cast(available_spaces as integer)
        end) * 100.0 / nullif(case
            when lower(location) like '%jernbanen%' then 400
            when lower(location) like '%forum%' then 350
            when lower(location) like '%sentrum%' then 350
            else 250
        end, 0)) as utilization_rate,

        -- Pricing (not provided by API)
        cast(null as double) as price_per_hour,

        -- Business logic
        case
            when extract(hour from try_cast(timestamp as timestamp)) between 7 and 9
              or extract(hour from try_cast(timestamp as timestamp)) between 16 and 18
            then 1
            else 0
        end as is_peak_hour,

        -- Additional API fields
        date as original_date,
        time as original_time,
        case
            when lower(location) like '%jernbanen%' then 'transport_hub'
            when lower(location) like '%forum%' then 'city_center'
            else 'residential'
        end as location_type,
        extract(hour from try_cast(timestamp as timestamp)) as hour,
        case extract(dow from try_cast(timestamp as timestamp))
            when 0 then 'Sunday'
            when 1 then 'Monday'
            when 2 then 'Tuesday'
            when 3 then 'Wednesday'
            when 4 then 'Thursday'
            when 5 then 'Friday'
            when 6 then 'Saturday'
        end as day_of_week,
        extract(month from try_cast(timestamp as timestamp)) as month,
        extract(year from try_cast(timestamp as timestamp)) as year,

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
    );

  