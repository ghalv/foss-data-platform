{#
  GOLD LAYER - PERFORMANCE REPORT QUALITY TESTS
  ===============================================
  Tests for data quality in the gold layer performance reports
#}

-- Test 1: Business logic validation
select
    'invalid_performance_score' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where overall_performance_score < 0 or overall_performance_score > 100

-- Test 2: Utilization rate consistency
select
    'utilization_bounds_violation' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where daily_avg_utilization < 0 or daily_avg_utilization > 100

-- Test 3: Status categorization consistency
select
    'inconsistent_status' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where (utilization_status = 'Critical - At Capacity' and daily_avg_utilization < 90)
   or (utilization_status = 'Moderate - Good Utilization' and daily_avg_utilization >= 90)

-- Test 4: Peak hour analysis validity
select
    'invalid_peak_analysis' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where peak_hour_percentage > 100 or peak_hour_percentage < 0

-- Test 5: Critical status percentage validation
select
    'invalid_critical_percentage' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where critical_status_percentage > 100 or critical_status_percentage < 0

-- Test 6: Business recommendation logic
select
    'inconsistent_recommendation' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where (business_recommendation = 'High Demand - Consider Expansion' and daily_avg_utilization < 80)
   or (business_recommendation = 'Very Low Demand - Strategic Review Needed' and daily_avg_utilization > 40)

-- Test 7: Operational recommendation consistency
select
    'inconsistent_operational_rec' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where (operational_recommendation = 'Consider Capacity Expansion' and at_capacity_count = 0)
   or (operational_recommendation = 'Address Peak Hour Constraints' and peak_constraint_count = 0)

-- Test 8: Data completeness for reporting
select
    'incomplete_report' as quality_issue,
    count(*) as affected_records
from {{ ref('gld_parking_performance_report') }}
where daily_avg_utilization is null
   or utilization_status is null
   or overall_performance_score is null
   or business_recommendation is null
