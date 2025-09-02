
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Test skipped: utilization_rate, occupancy, capacity not available in live feed
select 0 as calculation_errors
  
  
      
    ) dbt_internal_test