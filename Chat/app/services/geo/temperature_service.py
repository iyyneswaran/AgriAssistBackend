from datetime import datetime, timedelta
from .gee_client import get_gee_client


class TemperatureService:

    def __init__(self):
        self.ee = get_gee_client().get_ee()

    def get_temperature_forecast(self, latitude: float, longitude: float, forecast_days: int = 4):
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=forecast_days)

        # Buffer the point by 1000 meters to ensure we capture some pixels
        geometry = self.ee.Geometry.Point([longitude, latitude]).buffer(1000)

        # Use GFS forecast data for temperature
        # 1. Filter by model run time (system:time_start / creation_time) to get the latest models
        # 2. Filter by forecast_time to get the predictions for the next 4 days
        forecast_start = start_date.timestamp() * 1000
        forecast_end = end_date.timestamp() * 1000

        collection = (
            self.ee.ImageCollection("NOAA/GFS0P25")
            .filterBounds(geometry)
            .filter(self.ee.Filter.date(start_date - timedelta(hours=24), start_date)) # Get recent model runs
            .filter(self.ee.Filter.rangeContains('forecast_time', forecast_start, forecast_end)) # Get future predictions
            .select("temperature_2m_above_ground")
        )

        # Get absolute max and absolute min temperatures over the 4-day forecast period
        max_temp_image = collection.max()
        min_temp_image = collection.min()

        max_stats = max_temp_image.reduceRegion(
            reducer=self.ee.Reducer.mean(),
            geometry=geometry,
            scale=5000,
            maxPixels=1e9
        ).getInfo()

        min_stats = min_temp_image.reduceRegion(
            reducer=self.ee.Reducer.mean(),
            geometry=geometry,
            scale=5000,
            maxPixels=1e9
        ).getInfo()

        max_temp = max_stats.get("temperature_2m_above_ground") if max_stats else None
        min_temp = min_stats.get("temperature_2m_above_ground") if min_stats else None

        return {
            "max_temp_celsius": round(max_temp, 2) if max_temp is not None else None,
            "min_temp_celsius": round(min_temp, 2) if min_temp is not None else None,
            "forecast_days": forecast_days
        }