select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "memory"."default_dbt_test__audit"."test_capacity_occupancy_logic"
    
      
    ) dbt_internal_test