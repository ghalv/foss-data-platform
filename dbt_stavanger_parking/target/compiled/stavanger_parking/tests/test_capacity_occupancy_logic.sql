-- Test for capacity vs occupancy logic
select 
    count(*) as invalid_records
from "memory"."default_staging"."stg_parking_data"
where current_occupancy > total_capacity