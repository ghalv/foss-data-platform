{{
  config(
    materialized='incremental',
    incremental_strategy='append',
    partition_by={
      "field": "load_date",
      "data_type": "date"
    },
    tags=['metadata', 'audit', 'delta_load']
  )
}}

{#
  LOAD METADATA TABLE
  Tracks all delta load operations for audit and monitoring
  This showcases sophisticated metadata management in Iceberg
#}

select
  -- Load identification
  {{ var('pipeline_run_id', 'UNKNOWN') }} as load_id,
  current_timestamp as load_timestamp,
  date(current_timestamp) as load_date,

  -- Load metrics
  {{ var('record_count', 0) }} as records_processed,
  {{ var('load_duration_seconds', 0) }} as load_duration_seconds,
  {{ var('data_quality_score', 0) }} as data_quality_score,

  -- Load type and status
  {{ var('load_type', 'unknown') }} as load_type,
  'success' as load_status,

  -- Incremental tracking
  {{ var('last_load_timestamp', null) }} as last_load_timestamp,
  case
    when {{ var('last_load_timestamp', null) }} is not null then 'incremental'
    else 'initial'
  end as load_mode,

  -- Source information
  {{ var('data_source', 'unknown') }} as data_source,
  'stavanger_parking' as pipeline_name,
  'delta_load' as load_strategy,

  -- Environment and version info
  {{ dbt_version }} as dbt_version,
  {{ target.name }} as target_environment,

  -- Audit columns
  current_timestamp as _loaded_at,
  'load_metadata' as _model_type,
  '{{ invocation_id }}' as _dbt_invocation_id

{% if is_incremental() %}
union all

-- Handle failed loads (if any)
select
  load_id,
  load_timestamp,
  load_date,
  records_processed,
  load_duration_seconds,
  data_quality_score,
  load_type,
  'failed' as load_status,
  last_load_timestamp,
  load_mode,
  data_source,
  pipeline_name,
  load_strategy,
  dbt_version,
  target_environment,
  _loaded_at,
  _model_type,
  _dbt_invocation_id

from {{ this }}
where load_status = 'running'
  and load_timestamp < current_timestamp - interval '1' hour  -- Mark as failed if running for >1 hour
{% endif %}
