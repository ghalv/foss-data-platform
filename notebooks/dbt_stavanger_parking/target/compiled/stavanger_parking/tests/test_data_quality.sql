-- Data Quality Tests for Stavanger Parking Pipeline
-- These tests ensure data integrity and business logic validation

-- Test 1: Check for null values in critical fields
select 
    count(*) as null_count,
    'stg_parking_data' as table_name,
    'critical_fields_have_nulls' as test_name
from "memory"."default_staging"."stg_parking_data"
where parking_record_id is null 
   or recorded_at is null 
   or parking_location is null 
   or total_capacity is null 
   or current_occupancy is null

-- Test 2: Validate capacity vs occupancy logic
select 
    count(*) as invalid_records,
    'stg_parking_data' as table_name,
    'capacity_occupancy_logic' as test_name
from "memory"."default_staging"."stg_parking_data"
where current_occupancy > total_capacity

-- Test 3: Check utilization rate calculations
select 
    count(*) as calculation_errors,
    'stg_parking_data' as table_name,
    'utilization_rate_calculation' as test_name
from "memory"."default_staging"."stg_parking_data"
where abs(utilization_rate - (current_occupancy::float / total_capacity * 100)) > 0.01

-- Test 4: Validate time period logic
select 
    count(*) as time_period_errors,
    'stg_parking_data' as table_name,
    'time_period_categorization' as test_name
from "memory"."default_staging"."stg_parking_data"
where time_period is null

-- Test 5: Check for duplicate records
select 
    count(*) as duplicate_count,
    'stg_parking_data' as table_name,
    'duplicate_records' as test_name
from (
    select parking_record_id, count(*) as cnt
    from "memory"."default_staging"."stg_parking_data"
    group by parking_record_id
    having count(*) > 1
) duplicates

-- Test 6: Validate business logic for occupancy status
select 
    count(*) as status_logic_errors,
    'stg_parking_data' as table_name,
    'occupancy_status_logic' as test_name
from "memory"."default_staging"."stg_parking_data"
where occupancy_status is null

-- Test 7: Check for reasonable price ranges
select 
    count(*) as price_range_errors,
    'stg_parking_data' as table_name,
    'price_range_validation' as test_name
from "memory"."default_staging"."stg_parking_data"
where price_per_hour < 0 or price_per_hour > 100

-- Test 8: Validate location data consistency
select 
    count(*) as location_consistency_errors,
    'stg_parking_data' as table_name,
    'location_consistency' as test_name
from "memory"."default_staging"."stg_parking_data"
where parking_location is null or trim(parking_location) = ''