select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "memory"."default_dbt_test__audit"."test_utilization_rate_calculation"
    
      
    ) dbt_internal_test