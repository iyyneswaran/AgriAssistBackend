import sys
import os
import datetime
from datetime import timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
from app.services.geo.gee_client import get_gee_client

ee = get_gee_client().get_ee()
collection = ee.ImageCollection("NOAA/GFS0P25")

# Test 2: Let's test the specific query for today + 4 days
start_date = datetime.datetime.utcnow()
end_date = start_date + timedelta(days=4)

print(f"Querying from {start_date} to {end_date}")

geom = ee.Geometry.Point([80.16909638306561, 12.914672590797714]).buffer(1000)

forecast_start = start_date.timestamp() * 1000
forecast_end = end_date.timestamp() * 1000

filtered = collection.filterBounds(geom).filter(ee.Filter.date(start_date - timedelta(hours=24), start_date)).filter(ee.Filter.rangeContains('forecast_time', forecast_start, forecast_end))

print("Number of images in filtered collection:", filtered.size().getInfo())

count = filtered.size().getInfo()
if count > 0:
    first_image = filtered.first()
    print("Bands in first filtered image:", first_image.bandNames().getInfo())
    
    # Try the temperature reduction
    temp_image = filtered.select("temperature_2m_above_ground").max()
    stats = temp_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=5000,
        maxPixels=1e9
    ).getInfo()
    print("Max Temp Stats:", stats)
    
    # Try the rainfall reduction
    rain_image = filtered.select("precipitation_rate").sum()
    rain_stats = rain_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=5000,
        maxPixels=1e9
    ).getInfo()
    
    # Scale from kg/m^2/s to mm (assuming 3 hr intervals)
    if rain_stats and "precipitation_rate" in rain_stats:
        print("Raw Rainfall sum stats (rate):", rain_stats)
        print("Estimated Total Rainfall (mm):", rain_stats["precipitation_rate"] * 10800)
    else:
        print("Rainfall stats unavailable.")



