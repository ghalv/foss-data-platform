{#
  SILVER LAYER - OCCUPANCY FACTS QUALITY TESTS
  ==============================================
  Tests for data quality in the silver layer occupancy facts
#}

-- Test 1: Primary key uniqueness
select
    occupancy_key,
    count(*) as duplicate_count
from {{ ref('slv_parking_occupancy_facts') }}
group by occupancy_key
having count(*) > 1

-- Test 2: Referential integrity with locations
select
    'orphaned_fact' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }} f
left join {{ ref('slv_parking_locations') }} l on f.location_key = l.location_key
where l.location_key is null

-- Test 3: Business rule validation
select
    'invalid_utilization' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }}
where utilization_percentage < 0 or utilization_percentage > 150

-- Test 4: Capacity consistency
select
    'capacity_exceeded' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }} f
join {{ ref('slv_parking_locations') }} l on f.location_key = l.location_key
where f.occupied_spaces > l.estimated_capacity * 1.5  -- Allow 50% over-capacity

-- Test 5: Time series continuity
select
    location_key,
    recorded_date,
    count(*) as readings_per_day
from {{ ref('slv_parking_occupancy_facts') }}
group by location_key, recorded_date
having count(*) < 6  -- Less than 6 readings per day (every 4 hours minimum)
order by location_key, recorded_date

-- Test 6: Peak hour logic validation
select
    'invalid_peak_hour_logic' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }}
where (is_peak_hour = true and recorded_hour not between 7 and 9 and recorded_hour not between 16 and 19)
   or (is_peak_hour = false and recorded_hour between 7 and 9 or recorded_hour between 16 and 19)

-- Test 7: Data completeness
select
    'incomplete_fact' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }}
where utilization_percentage is null
   or available_spaces is null
   or occupied_spaces is null

-- Test 8: Temporal consistency
select
    'future_timestamp' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }}
where recorded_timestamp > current_timestamp + interval '1 hour'

union all

select
    'old_timestamp' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_occupancy_facts') }}
where recorded_timestamp < current_date - interval '30 days'
