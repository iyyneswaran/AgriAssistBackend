from datetime import datetime, timedelta
from .gee_client import get_gee_client
from .rainfall_classifier import build_classification


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
        # 2. Filter by forecast_time to get the predictions for the next N days
        forecast_start = start_date.timestamp() * 1000
        forecast_end = end_date.timestamp() * 1000

        collection = (
            self.ee.ImageCollection("NOAA/GFS0P25")
            .filterBounds(geometry)
            .filter(self.ee.Filter.date(start_date - timedelta(hours=24), start_date))  # Recent model runs
            .filter(self.ee.Filter.rangeContains('forecast_time', forecast_start, forecast_end))  # Future predictions
            .select("precipitation_rate")
        )

        # ─── Get cumulative 4-day total (preserves existing behavior) ────
        rainfall_sum = collection.sum()

        stats = rainfall_sum.reduceRegion(
            reducer=self.ee.Reducer.mean(),
            geometry=geometry,
            scale=5000,
            maxPixels=1e9
        )

        stats_dict = stats.getInfo()
        rate_sum = stats_dict.get("precipitation_rate") if stats_dict else None

        # precipitation_rate is in kg/m^2/s (mm/s).
        # Multiply the sum of rates by 3600 seconds (per the verified fix).
        cumulative_mm = rate_sum * 3600 if rate_sum is not None else 0

        # ─── Get daily breakdown ─────────────────────────────────────────
        daily_totals = []
        try:
            for day_offset in range(forecast_days):
                day_start = start_date + timedelta(days=day_offset)
                day_end = start_date + timedelta(days=day_offset + 1)
                day_fstart = day_start.timestamp() * 1000
                day_fend = day_end.timestamp() * 1000

                day_collection = (
                    self.ee.ImageCollection("NOAA/GFS0P25")
                    .filterBounds(geometry)
                    .filter(self.ee.Filter.date(start_date - timedelta(hours=24), start_date))
                    .filter(self.ee.Filter.rangeContains('forecast_time', day_fstart, day_fend))
                    .select("precipitation_rate")
                )

                day_sum = day_collection.sum()
                day_stats = day_sum.reduceRegion(
                    reducer=self.ee.Reducer.mean(),
                    geometry=geometry,
                    scale=5000,
                    maxPixels=1e9
                ).getInfo()

                day_rate = day_stats.get("precipitation_rate") if day_stats else None
                day_mm = day_rate * 3600 if day_rate is not None else 0
                daily_totals.append(day_mm)
        except Exception as e:
            print(f"Warning: Could not get daily breakdown: {e}")
            daily_totals = None  # Fall back to average split

        # ─── Build classified response ───────────────────────────────────
        # Pass soil_moisture_mm=None here; it will be injected by geo_analysis_service
        classification = build_classification(
            cumulative_mm=cumulative_mm,
            forecast_days=forecast_days,
            daily_totals=daily_totals,
        )

        # Return the full classification dict plus backward-compatible fields
        result = classification.to_dict()
        # Keep backward-compatible keys so existing consumers don't break
        result["forecast_rainfall_mm"] = classification.cumulative_mm
        result["forecast_days"] = forecast_days

        return result