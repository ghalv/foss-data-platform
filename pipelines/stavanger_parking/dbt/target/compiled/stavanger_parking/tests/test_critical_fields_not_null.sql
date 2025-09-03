-- Test for null values in critical fields (aligned to raw_parking_data schema)
-- Returns rows that have null values in critical fields (should return 0 rows to pass)
select
    parking_record_id,
    parking_location,
    recorded_at,
    available_spaces,
    total_capacity,
    current_occupancy
from "iceberg"."analytics_staging"."stg_parking_data"
where parking_record_id is null
   or recorded_at is null
   or parking_location is null
   or available_spaces is null
   or total_capacity is null
   or current_occupancy is null