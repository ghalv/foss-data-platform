
  create or replace view
    "memory"."default"."test_simple"
  security definer
  as
    SELECT 1 as test_column
  ;
