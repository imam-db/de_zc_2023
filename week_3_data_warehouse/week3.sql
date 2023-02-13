-- No. 1

SELECT COUNT(*) AS total_data
FROM `de-learning-2023.trips_data_all.fhv`;

-- No. 2

```sql
-- call external table
SELECT COUNT(DISTINCT Affiliated_base_number) AS total_distinct_affiliated
FROM `trips_data_all.fhv_external`;

-- call native table
SELECT COUNT(DISTINCT Affiliated_base_number) AS total_distinct_affiliated
FROM `trips_data_all.fhv_native`;
```

-- No. 3

```sql
SELECT COUNT(*) AS total_null
FROM `trips_data_all.fhv_external`
WHERE PUlocationID IS NULL AND DOlocationID IS NULL;
```



-- No. 5

```sql
CREATE OR REPLACE TABLE trips_data_all.fhv_native_partitioned
PARTITION BY DATE(pickup_datetime) AS
SELECT *
FROM `trips_data_all.fhv_native`;

# without partition
SELECT DISTINCT Affiliated_base_number
FROM `trips_data_all.fhv_native`
WHERE pickup_datetime BETWEEN '2019-03-01' AND '2019-03-31';

# with partition
SELECT DISTINCT Affiliated_base_number
FROM `trips_data_all.fhv_native_partitioned`
WHERE pickup_datetime BETWEEN '2019-03-01' AND '2019-03-31';
```