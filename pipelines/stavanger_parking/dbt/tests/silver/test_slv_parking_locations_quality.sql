{#
  SILVER LAYER - PARKING LOCATIONS QUALITY TESTS
  ================================================
  Tests for data quality in the silver layer parking locations
#}

-- Test 1: Primary key uniqueness
select
    location_key,
    count(*) as duplicate_count
from {{ ref('slv_parking_locations') }}
group by location_key
having count(*) > 1

-- Test 2: Referential integrity
select
    'orphaned_location' as quality_issue,
    count(distinct f.location_key) as affected_locations
from {{ ref('slv_parking_occupancy_facts') }} f
left join {{ ref('slv_parking_locations') }} l on f.location_key = l.location_key
where l.location_key is null

-- Test 3: Business rule validation
select
    'invalid_capacity' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_locations') }}
where estimated_capacity <= 0 or estimated_capacity > 2000

-- Test 4: Geographic validation
select
    'invalid_coordinates' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_locations') }}
where latitude is not null and longitude is not null
  and (latitude < 58.0 or latitude > 60.0     -- Stavanger latitude bounds
   or longitude < 5.0 or longitude > 6.0)     -- Stavanger longitude bounds

-- Test 5: Data completeness
select
    'incomplete_location' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_locations') }}
where location_name is null
   or location_category is null
   or business_segment is null

-- Test 6: Category consistency
select
    'invalid_category' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_locations') }}
where location_category not in ('transport_hub', 'city_center', 'residential', 'recreational')

-- Test 7: Operational status validation
select
    'invalid_operational_status' as quality_issue,
    count(*) as affected_records
from {{ ref('slv_parking_locations') }}
where operational_status not in ('active', 'inactive_recent', 'inactive')
