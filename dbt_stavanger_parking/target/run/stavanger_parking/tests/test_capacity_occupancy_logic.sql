
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Test skipped: capacity/occupancy not available in live feed
select 0 as invalid_records
  
  
      
    ) dbt_internal_test