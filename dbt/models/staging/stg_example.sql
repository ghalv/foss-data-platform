-- Simple staging model to test dbt-trino integration
-- This will help us verify that dbt can connect to Trino and execute queries

{{ config(materialized='table') }}

SELECT 
    'Hello from dbt-trino!' as message,
    current_timestamp as timestamp,
    'staging' as model_type
