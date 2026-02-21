from datetime import datetime, timedelta
from .gee_client import get_gee_client


class RainfallService:

    def __init__(self):
        self.ee = get_gee_client().get_ee()

    def get_rainfall_forecast(self, latitude: float, longitude: float, forecast_days: int = 4):
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=forecast_days)

        # Buffer the point by 1000 meters
        geometry = self.ee.Geometry.Point([longitude, latitude]).buffer(1000)

        # Use GFS forecast data for precipitation
        # 1. Filter by creation_time to get the latest model run (within the last 24 hours)
        # 2. Filter by forecast_time to get the predictions for the next 4 days
        creation_start = (start_date - timedelta(hours=24)).timestamp() * 1000
        creation_end = start_date.timestamp() * 1000
        forecast_start = start_date.timestamp() * 1000
        forecast_end = end_date.timestamp() * 1000

        collection = (
            self.ee.ImageCollection("NOAA/GFS0P25")
            .filterBounds(geometry)
            .filter(self.ee.Filter.date(start_date - timedelta(hours=24), start_date)) # Get recent model runs
            .filter(self.ee.Filter.rangeContains('forecast_time', forecast_start, forecast_end)) # Get future predictions
            .select("total_precipitation_surface")
        )

        # Sum the precipitation forecasts over the period
        rainfall_sum = collection.sum()

        stats = rainfall_sum.reduceRegion(
            reducer=self.ee.Reducer.mean(),
            geometry=geometry,
            scale=5000,
            maxPixels=1e9
        )

        stats_dict = stats.getInfo()
        rainfall_value = stats_dict.get("total_precipitation_surface") if stats_dict else None

        return {
            "forecast_rainfall_mm": round(rainfall_value, 2) if rainfall_value is not None else 0,
            "forecast_days": forecast_days
        }