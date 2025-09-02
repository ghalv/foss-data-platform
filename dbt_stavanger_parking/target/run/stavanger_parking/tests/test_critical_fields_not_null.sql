
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Test for null values in critical fields (aligned to live schema)
select 
    count(*) as null_count
from "memory"."default_staging"."stg_parking_data"
where parking_record_id is null 
   or recorded_at is null 
   or parking_location is null 
   or available_spaces is null
  
  
      
    ) dbt_internal_test