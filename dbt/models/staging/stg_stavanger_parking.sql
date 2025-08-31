-- Staging model for Stavanger parking data
-- This will be populated by our Dagster pipeline

{{ config(materialized='table') }}

WITH source_data AS (
    SELECT 
        -- Raw data fields (will be populated by Dagster)
        'placeholder' as parking_house_name,
        'placeholder' as location,
        0 as available_spaces,
        0 as total_spaces,
        current_timestamp as last_updated,
        'staging' as data_source
)

SELECT 
    parking_house_name,
    location,
    available_spaces,
    total_spaces,
    last_updated,
    data_source,
    -- Add some computed fields
    (total_spaces - available_spaces) as occupied_spaces,
    CASE 
        WHEN total_spaces > 0 THEN (CAST(available_spaces AS DOUBLE) / CAST(total_spaces AS DOUBLE)) * 100
        ELSE 0 
    END as occupancy_percentage
FROM source_data
