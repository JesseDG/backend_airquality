from influxdb import client as client_module

RANGES = {
    "1h": {"start": "-1h", "aggregate": None},
    "24h": {"start": "-24h", "aggregate": "5m"},
    "1w": {"start": "-7d", "aggregate": "1h"},
    "1m": {"start": "-30d", "aggregate": "6h"},
}

async def get_history(range: str, sensor: str, device_id: str):
    #check if range is valid
    config_range = RANGES.get(range)
    if not config_range:
        return {"error": "Invalid range. Valid options are: " + ", ".join(RANGES.keys())}
    
    start = config_range["start"]
    aggregate = config_range["aggregate"]

    query = f"""
        from(bucket: "{client_module.INFLUXDB_BUCKET}")
            |> range(start: {start})
            |> filter(fn: (r) => r["_measurement"] == "air_quality_data")
            |> filter(fn: (r) => r["device_id"] == "{device_id}")
            |> filter(fn: (r) => r["_field"] == "{sensor}") 
        """
    if aggregate:
        query += f'|> aggregateWindow(every: {aggregate}, fn: mean, createEmpty: false)'
    
    tables = client_module.client.query_api().query(query, org=client_module.INFLUXDB_ORG)
    results = []
    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time(),
                "value": record.get_value()
            })

    return {"message": f"Historical data for range {range} for gas {sensor} and device {device_id}", "data": results}