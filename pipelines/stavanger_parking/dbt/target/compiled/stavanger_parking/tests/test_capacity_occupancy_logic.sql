-- Test capacity/occupancy logic: occupancy should not exceed capacity
-- Returns rows that violate capacity/occupancy logic (should return 0 rows to pass)
select
    parking_record_id,
    parking_location,
    total_capacity,
    current_occupancy,
    available_spaces
from "memory"."parking_data_staging"."stg_parking_data"
where current_occupancy > total_capacity
   or available_spaces < 0
   or total_capacity < 0
   or current_occupancy < 0