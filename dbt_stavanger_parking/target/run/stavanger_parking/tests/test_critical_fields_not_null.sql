select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "memory"."default_dbt_test__audit"."test_critical_fields_not_null"
    
      
    ) dbt_internal_test