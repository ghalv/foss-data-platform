
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Test utilization rate calculation: (occupancy / capacity) * 100 should match utilization_rate
-- Returns rows where utilization rate calculation doesn't match (should return 0 rows to pass)
select
    parking_record_id,
    parking_location,
    total_capacity,
    current_occupancy,
    utilization_rate,
    (current_occupancy * 100.0 / nullif(total_capacity, 0)) as calculated_rate
from "memory"."default_staging"."stg_parking_data"
where abs(utilization_rate - (current_occupancy * 100.0 / nullif(total_capacity, 0))) > 0.01
  and total_capacity > 0  -- Only test where capacity is available
  
  
      
    ) dbt_internal_test