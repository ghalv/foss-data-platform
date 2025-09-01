
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Test for capacity vs occupancy logic
select 
    count(*) as invalid_records
from "memory"."default_staging"."stg_parking_data"
where current_occupancy > total_capacity
  
  
      
    ) dbt_internal_test