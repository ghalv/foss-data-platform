{#
  BRONZE LAYER - RAW PARKING DATA QUALITY TESTS
  ===============================================
  Tests for data quality in the bronze layer raw data
#}

-- Test 1: Primary key uniqueness
select
    merge_key,
    count(*) as duplicate_count
from {{ ref('brz_raw_parking_data') }}
group by merge_key
having count(*) > 1

-- Test 2: Required fields not null
select
    'missing_timestamp' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where recorded_timestamp is null
union all
select
    'missing_location' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where location is null
union all
select
    'missing_spaces' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where available_spaces_int is null

-- Test 3: Data type validation
select
    'invalid_timestamp' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where recorded_timestamp is not null
  and recorded_timestamp < '2020-01-01'::timestamp
   or recorded_timestamp > current_timestamp + interval '1 hour'

-- Test 4: Geographic bounds validation
select
    'invalid_latitude' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where latitude_double is not null
  and (latitude_double < 50 or latitude_double > 75)  -- Norway bounds

union all

select
    'invalid_longitude' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where longitude_double is not null
  and (longitude_double < 0 or longitude_double > 30)  -- Norway bounds

-- Test 5: Business rule validation
select
    'negative_spaces' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where available_spaces_int < 0

-- Test 6: Data freshness
select
    'stale_data' as quality_issue,
    count(*) as affected_records
from {{ ref('brz_raw_parking_data') }}
where recorded_timestamp < current_timestamp - interval '24 hours'
