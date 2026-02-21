from .ndvi_service import NDVIService
from .rainfall_service import RainfallService
from .temperature_service import TemperatureService


class GeoAnalysisService:

    def __init__(self):
        self.ndvi_service = NDVIService()
        self.rainfall_service = RainfallService()
        self.temperature_service = TemperatureService()

    def analyze(self, latitude: float, longitude: float):
        ndvi_data = self.ndvi_service.calculate_ndvi(latitude, longitude)
        rainfall_data = self.rainfall_service.get_rainfall_forecast(latitude, longitude)
        temperature_data = self.temperature_service.get_temperature_forecast(latitude, longitude)

        alerts = self._generate_alerts(
            rainfall_data.get("forecast_rainfall_mm"),
            temperature_data.get("max_temp_celsius"),
            temperature_data.get("min_temp_celsius")
        )

        return {
            "ndvi": ndvi_data,
            "rainfall_forecast": rainfall_data,
            "temperature_forecast": temperature_data,
            "alerts": alerts
        }

    def _generate_alerts(self, rainfall: float, max_temp: float, min_temp: float):
        alerts = []
        
        # Rainfall Alerts
        if rainfall is not None:
            if rainfall > 50:
                alerts.append("High Flood Risk: Heavy rainfall expected.")
            elif rainfall > 20:
                alerts.append("Moderate Rain Expected.")
        
        # Temperature Alerts
        if max_temp is not None:
            if max_temp > 35:
                alerts.append(f"Heat Advisory: High temperatures up to {max_temp}°C expected.")
        
        if min_temp is not None:
            if min_temp < 10:
                alerts.append(f"Cold Warning: Temperatures dropping to {min_temp}°C.")

        if not alerts:
            alerts.append("No immediate weather risks detected.")

        return alerts