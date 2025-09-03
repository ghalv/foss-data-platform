
  create or replace view
    "iceberg"."analytics"."test_model"
  security definer
  as
    SELECT 1 as test_column
  ;
