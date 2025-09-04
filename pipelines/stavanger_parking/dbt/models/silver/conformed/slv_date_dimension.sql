{{
  config(
    materialized='table',
    schema='analytics_staging',
    tags=['silver', 'conformed', 'dimension', 'dates', 'calendar']
  )
}}

{#
  SILVER LAYER - DATE DIMENSION (CONFORMED)
  ===========================================
  Purpose: Standardized date dimension for consistent time-based analytics
  Principles:
  - Conformed dimension across all facts
  - Rich calendar attributes
  - Business calendar logic
  - Pre-computed for performance
#}

with date_series as (
  -- Generate date series for next 2 years
  select
    date_add('day', seq, current_date) as date_key
  from unnest(sequence(0, 730)) as t(seq)  -- 2 years
),

date_attributes as (
  select
    date_key,

    -- Basic date components
    year(date_key) as year,
    month(date_key) as month,
    day(date_key) as day,
    dayofweek(date_key) as day_of_week,
    week(date_key) as week_of_year,
    quarter(date_key) as quarter,

    -- Formatted date strings
    date_format(date_key, 'yyyy-MM-dd') as date_iso,
    date_format(date_key, 'dd/MM/yyyy') as date_eu,
    date_format(date_key, 'MM/dd/yyyy') as date_us,

    -- Day attributes
    case dayofweek(date_key)
      when 1 then 'Monday'
      when 2 then 'Tuesday'
      when 3 then 'Wednesday'
      when 4 then 'Thursday'
      when 5 then 'Friday'
      when 6 then 'Saturday'
      when 7 then 'Sunday'
    end as day_name,

    case
      when dayofweek(date_key) in (1,2,3,4,5) then 'Weekday'
      else 'Weekend'
    end as day_type,

    case
      when dayofweek(date_key) = 1 then true
      else false
    end as is_monday,

    case
      when dayofweek(date_key) = 7 then true
      else false
    end as is_sunday,

    -- Month attributes
    case month(date_key)
      when 1 then 'January'
      when 2 then 'February'
      when 3 then 'March'
      when 4 then 'April'
      when 5 then 'May'
      when 6 then 'June'
      when 7 then 'July'
      when 8 then 'August'
      when 9 then 'September'
      when 10 then 'October'
      when 11 then 'November'
      when 12 then 'December'
    end as month_name,

    case
      when month(date_key) in (12,1,2) then 'Winter'
      when month(date_key) in (3,4,5) then 'Spring'
      when month(date_key) in (6,7,8) then 'Summer'
      when month(date_key) in (9,10,11) then 'Autumn'
    end as season,

    -- Quarter attributes
    concat('Q', quarter(date_key)) as quarter_name,
    case
      when quarter(date_key) in (1,4) then 'End Quarter'
      else 'Mid Quarter'
    end as quarter_type,

    -- Business calendar (Norwegian context)
    case
      when month(date_key) = 12 and day(date_key) >= 24 then true
      when month(date_key) = 1 and day(date_key) <= 2 then true
      else false
    end as is_holiday_season,

    -- Parking-specific business periods
    case
      when dayofweek(date_key) in (1,2,3,4,5)
           and hour(current_time) between 7 and 18 then true
      else false
    end as is_business_hours,

    -- Weekend indicators
    case
      when dayofweek(date_key) in (6,7) then true
      else false
    end as is_weekend,

    -- Fiscal year (assuming July 1 start for Norway)
    case
      when month(date_key) >= 7 then year(date_key)
      else year(date_key) - 1
    end as fiscal_year,

    case
      when month(date_key) >= 7 then month(date_key) - 6
      else month(date_key) + 6
    end as fiscal_month,

    -- Metadata
    current_timestamp as _created_at,
    'silver_conformed' as _layer,
    'calendar_generator' as _source_system

  from date_series
)

select * from date_attributes
order by date_key
