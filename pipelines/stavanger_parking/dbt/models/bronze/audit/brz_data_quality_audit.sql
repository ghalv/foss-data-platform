{{
  config(
    materialized='incremental',
    incremental_strategy='append',
    schema='analytics_staging',
    tags=['bronze', 'audit', 'data_quality', 'monitoring']
  )
}}

{#
  BRONZE LAYER - DATA QUALITY AUDIT
  ===================================
  Purpose: Track data quality metrics and pipeline health
  Principles:
  - Comprehensive quality monitoring
  - Pipeline execution tracking
  - Error and anomaly detection
  - Trend analysis capabilities
#}

with pipeline_metrics as (
  select
    {{ var('pipeline_run_id', 'unknown') }} as pipeline_run_id,
    current_timestamp as audit_timestamp,

    -- Pipeline metadata
    '{{ invocation_id }}' as dbt_invocation_id,
    '{{ run_started_at }}' as pipeline_start_time,

    -- Source data summary
    count(*) as total_records_received,
    count(distinct merge_key) as unique_records,
    count(distinct location) as unique_locations,

    -- Data quality breakdown
    sum(has_valid_timestamp) as records_with_valid_timestamp,
    sum(has_valid_spaces) as records_with_valid_spaces,
    sum(has_valid_coordinates) as records_with_valid_coordinates,

    -- Completeness percentages
    round((sum(has_valid_timestamp) * 100.0) / count(*), 2) as timestamp_completeness_pct,
    round((sum(has_valid_spaces) * 100.0) / count(*), 2) as spaces_completeness_pct,
    round((sum(has_valid_coordinates) * 100.0) / count(*), 2) as coordinates_completeness_pct,

    -- Quality score (weighted average)
    round((
      (sum(has_valid_timestamp) * 0.4) +
      (sum(has_valid_spaces) * 0.4) +
      (sum(has_valid_coordinates) * 0.2)
    ) * 100.0 / count(*), 2) as overall_quality_score

  from {{ ref('brz_raw_parking_data') }}
  where _bronze_loaded_at >= '{{ run_started_at }}'
),

data_anomalies as (
  select
    pipeline_run_id,

    -- Statistical anomalies
    avg(available_spaces_int) as avg_spaces,
    stddev(available_spaces_int) as std_spaces,
    min(available_spaces_int) as min_spaces,
    max(available_spaces_int) as max_spaces,

    -- Geographic anomalies
    count(case when latitude_double < 50 or latitude_double > 75 then 1 end) as invalid_latitude_count,
    count(case when longitude_double < 0 or longitude_double > 30 then 1 end) as invalid_longitude_count,

    -- Time-based anomalies
    count(case when recorded_timestamp < current_date - interval '30' day then 1 end) as old_timestamp_count,
    count(case when recorded_timestamp > current_timestamp + interval '1' hour then 1 end) as future_timestamp_count

  from {{ ref('brz_raw_parking_data') }}
  where _bronze_loaded_at >= '{{ run_started_at }}'
  group by pipeline_run_id
),

final_audit as (
  select
    pm.*,

    -- Anomaly indicators
    da.avg_spaces,
    da.std_spaces,
    da.min_spaces,
    da.max_spaces,
    da.invalid_latitude_count,
    da.invalid_longitude_count,
    da.old_timestamp_count,
    da.future_timestamp_count,

    -- Quality thresholds
    case
      when pm.overall_quality_score >= 95 then 'Excellent'
      when pm.overall_quality_score >= 85 then 'Good'
      when pm.overall_quality_score >= 75 then 'Fair'
      else 'Poor'
    end as quality_rating,

    case
      when da.invalid_latitude_count > 0 or da.invalid_longitude_count > 0 then 'Geographic Anomalies'
      when da.old_timestamp_count > 0 or da.future_timestamp_count > 0 then 'Temporal Anomalies'
      else 'Normal'
    end as anomaly_status,

    -- Metadata
    'bronze_audit' as _layer,
    current_timestamp as _audit_created_at

  from pipeline_metrics pm
  left join data_anomalies da on pm.pipeline_run_id = da.pipeline_run_id
)

select * from final_audit
