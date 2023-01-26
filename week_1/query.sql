-- How many taxi trips were totally made on January 15?

SELECT COUNT(*) AS total_trips
FROM public.tripdata AS td
WHERE td.lpep_pickup_datetime BETWEEN  '2019-01-15 00:00:00' AND '2019-01-15 23:59:59'
AND td.lpep_dropoff_datetime BETWEEN  '2019-01-15 00:00:00' AND '2019-01-15 23:59:59';

-- Which was the day with the largest trip distance? Use the pick up time for your calculations.

SELECT td.lpep_pickup_datetime::date AS date_trip,
	MAX(trip_distance) AS largest_distance
FROM public.tripdata AS td
GROUP BY td.lpep_pickup_datetime::date
ORDER BY largest_distance DESC
LIMIT 1;

-- In 2019-01-01 how many trips had 2 and 3 passengers?

SELECT COUNT(CASE WHEN td.passenger_count = 2 THEN passenger_count END) AS passenger_2,
	COUNT(CASE WHEN td.passenger_count = 3 THEN passenger_count END) AS passenger_3
FROM public.tripdata AS td
WHERE td.lpep_pickup_datetime::date = '2019-01-01';

-- For the passengers picked up in the Astoria Zone which was the drop off zone that had the largest tip? 
-- We want the name of the zone, not the id.

SELECT tz_do."Zone" AS dropout_zone,
	MAX(td.tip_amount) AS max_tip
FROM public.tripdata AS td
INNER JOIN public.taxi_zone AS tz_pu
	ON td."PULocationID" = tz_pu."LocationID"
INNER JOIN public.taxi_zone AS tz_do
	ON td."DOLocationID" = tz_do."LocationID"
WHERE tz_pu."Zone" = 'Astoria'
GROUP BY tz_do."Zone"
ORDER BY max_tip DESC
LIMIT 1;