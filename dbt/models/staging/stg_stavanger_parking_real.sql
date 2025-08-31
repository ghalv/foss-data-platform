-- Real Stavanger parking data model
-- This will be populated by our Dagster pipeline with actual data

{{ config(materialized='table') }}

WITH source_data AS (
    SELECT 
        -- This will be replaced by actual data from Dagster
        -- For now, using placeholder data for testing
        'Stavanger Sentrum' as parking_house_name,
        '58.9700,5.7331' as location,
        45 as available_spaces,
        200 as total_spaces,
        current_timestamp as last_updated,
        'stavanger_parking_api' as data_source,
        current_timestamp as ingestion_timestamp,
        'test_run' as pipeline_run_id
)

SELECT 
    parking_house_name,
    location,
    available_spaces,
    total_spaces,
    last_updated,
    data_source,
    ingestion_timestamp,
    pipeline_run_id,
    -- Computed fields
    (total_spaces - available_spaces) as occupied_spaces,
    CASE 
        WHEN total_spaces > 0 THEN (CAST(available_spaces AS DOUBLE) / CAST(total_spaces AS DOUBLE)) * 100
        ELSE 0 
    END as occupancy_percentage,
    -- Data quality indicators
    CASE 
        WHEN available_spaces >= 0 AND total_spaces > 0 AND available_spaces <= total_spaces THEN 'valid'
        ELSE 'invalid'
    END as data_quality_status,
    -- Geographic fields (extracted from coordinates)
    SPLIT(location, ',')[1] as latitude,
    SPLIT(location, ',')[2] as longitude,
    -- Business logic
    CASE 
        WHEN available_spaces = 0 THEN 'full'
        WHEN available_spaces <= total_spaces * 0.1 THEN 'almost_full'
        WHEN available_spaces <= total_spaces * 0.5 THEN 'moderate'
        ELSE 'available'
    END as availability_status
FROM source_data
