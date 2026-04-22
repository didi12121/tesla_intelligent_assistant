# Telemetry Trip Stats Example

## 1) Ingest one telemetry point

```bash
curl -X POST "http://127.0.0.1:8001/api/telemetry/ingest" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWRpIiwiZXhwIjoxNzc2NzkxMjg1fQ.2qPpVTkWnfyUTUMLrhauP37gb6-yx1ML64iulJuGL_o" \
  -H "Content-Type: application/json" \
  -d "{\"vin\":\"LRWYGCFS5PC006410\",\"event_ts\":\"2026-04-20T09:00:00\",\"speed_kph\":42.5,\"odometer_km\":12345.6,\"battery_level\":78.5,\"latitude\":31.2304,\"longitude\":121.4737}"
```

## 2) Ingest batch points

```bash
curl -X POST "http://127.0.0.1:8000/api/telemetry/ingest/batch" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"vin\":\"LRWXXXXXXXXXXXXXX\",\"event_ts\":\"2026-04-20T09:00:00\",\"speed_kph\":12.3,\"odometer_km\":12345.6},{\"vin\":\"LRWXXXXXXXXXXXXXX\",\"event_ts\":\"2026-04-20T09:02:00\",\"speed_kph\":36.1,\"odometer_km\":12346.3}]}"
```

## 3) Query trip summary

```bash
curl -X GET "http://127.0.0.1:8000/api/telemetry/trips/summary?vin=LRWXXXXXXXXXXXXXX&start_ts=2026-04-20T00:00:00&end_ts=2026-04-20T23:59:59&stop_gap_minutes=5" \
  -H "Authorization: Bearer <your_jwt_token>"
```

Response includes:
- trip_count
- total_distance_km
- total_drive_minutes
- each trip with start/end time, distance, avg/max speed, battery usage

