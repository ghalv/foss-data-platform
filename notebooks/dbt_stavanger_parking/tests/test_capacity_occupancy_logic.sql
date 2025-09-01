-- Test for capacity vs occupancy logic
select 
    count(*) as invalid_records
from {{ ref('stg_parking_data') }}
where current_occupancy > total_capacity
