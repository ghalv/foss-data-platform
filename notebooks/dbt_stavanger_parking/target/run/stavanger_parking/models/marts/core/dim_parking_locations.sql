
  
    

    create table "memory"."default_marts_core"."dim_parking_locations__dbt_tmp"
      
      
    as (
      

with staging as (
    select distinct
        parking_location,
        parking_type,
        parking_zone,
        total_capacity,
        price_per_hour
    from "memory"."default_staging"."stg_parking_data"
),

final as (
    select
        -- Surrogate key (using row_number for simplicity)
        row_number() over (order by parking_location, parking_type, parking_zone) as location_key,
        
        -- Natural keys
        parking_location as location_name,
        parking_type,
        parking_zone,
        
        -- Attributes
        total_capacity as max_capacity,
        price_per_hour,
        
        -- Categorizations
        case 
            when parking_type = 'Garage' then 'Indoor'
            when parking_type = 'Surface' then 'Outdoor'
            else 'Street'
        end as location_category,
        
        case 
            when total_capacity >= 150 then 'Large'
            when total_capacity >= 75 then 'Medium'
            else 'Small'
        end as capacity_category,
        
        case 
            when price_per_hour >= 40 then 'Premium'
            when price_per_hour >= 25 then 'Standard'
            else 'Economy'
        end as pricing_tier,
        
        -- Metadata
        current_timestamp as _loaded_at,
        'dimension' as _model_type
        
    from staging
)

select * from final
    );

  