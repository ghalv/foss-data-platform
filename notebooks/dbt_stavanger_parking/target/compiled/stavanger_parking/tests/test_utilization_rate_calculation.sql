-- Test for utilization rate calculation accuracy
select 
    count(*) as calculation_errors
from "memory"."default_staging"."stg_parking_data"
where abs(utilization_rate - (CAST(current_occupancy AS DOUBLE) / total_capacity * 100)) > 0.01