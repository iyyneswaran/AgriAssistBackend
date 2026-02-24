from datetime import datetime, timedelta
from .gee_client import get_gee_client


class NDVIService:

    def __init__(self):
        self.ee = get_gee_client().get_ee()

    def calculate_ndvi(self, latitude: float, longitude: float, days: int = 30):
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Buffer the point by 100 meters (roughly a small farm area) to get an average rather than a single 10m pixel
        geometry = self.ee.Geometry.Point([longitude, latitude]).buffer(100)

        collection = (
            self.ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometry)
            .filterDate(start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"))
            .filter(self.ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        )

        image = collection.median()

        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

        stats = ndvi.reduceRegion(
            reducer=self.ee.Reducer.mean(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9
        )

        stats_dict = stats.getInfo()
        ndvi_mean = stats_dict.get("NDVI") if stats_dict else None

        health_status = self._classify_ndvi(ndvi_mean)

        return {
            "ndvi_mean": round(ndvi_mean, 3) if ndvi_mean else None,
            "health_status": health_status,
            "date_range_days": days
        }

    def _classify_ndvi(self, value):
        if value is None:
            return "No Data"
        if value < 0.2:
            return "Poor"
        elif value < 0.5:
            return "Moderate"
        else:
            return "Healthy"