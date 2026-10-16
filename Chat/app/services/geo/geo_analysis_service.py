from .ndvi_service import NDVIService
from .rainfall_service import RainfallService
from .temperature_service import TemperatureService
from .farm_metrics_service import FarmMetricsService
from .rainfall_classifier import (
    classify_24h_rainfall,
    assess_waterlogging_risk,
    RainfallSeverity,
    WaterloggingRisk,
)

class GeoAnalysisService:

    def __init__(self):
        self.ndvi_service = NDVIService()
        self.rainfall_service = RainfallService()
        self.temperature_service = TemperatureService()
        self.farm_metrics_service = FarmMetricsService()

    def analyze(self, latitude: float, longitude: float):
        ndvi_data = self.ndvi_service.calculate_ndvi(latitude, longitude)
        rainfall_data = self.rainfall_service.get_rainfall_forecast(latitude, longitude)
        temperature_data = self.temperature_service.get_temperature_forecast(latitude, longitude)
        farm_metrics = self.farm_metrics_service.get_metrics(latitude, longitude)

        # ─── Enrich waterlogging risk with soil moisture if available ─────
        soil_moisture_mm = farm_metrics.get("soil_moisture_mm") if farm_metrics else None
        if soil_moisture_mm is not None:
            enriched_risk = assess_waterlogging_risk(
                cumulative_mm=rainfall_data.get("cumulative_mm"),
                forecast_days=rainfall_data.get("forecast_days", 4),
                soil_moisture_mm=soil_moisture_mm,
            )
            rainfall_data["waterlogging_risk"] = enriched_risk.value

        alerts = self._generate_alerts(
            rainfall_data=rainfall_data,
            max_temp=temperature_data.get("max_temp_celsius"),
            min_temp=temperature_data.get("min_temp_celsius"),
        )

        return {
            "ndvi": ndvi_data,
            "rainfall_forecast": rainfall_data,
            "temperature_forecast": temperature_data,
            "farm_metrics": farm_metrics,
            "alerts": alerts
        }

    def _generate_alerts(self, rainfall_data: dict, max_temp: float, min_temp: float):
        """
        Generate weather alerts from classified rainfall data and temperature.
        
        Uses IMD-classified peak 24h severity and waterlogging risk
        instead of raw mm thresholds.
        """
        alerts = []

        # ─── Rainfall / Waterlogging Alerts ──────────────────────────────
        peak_severity = rainfall_data.get("peak_24h_severity", "unknown")
        waterlogging_risk = rainfall_data.get("waterlogging_risk", "unknown")
        peak_mm = rainfall_data.get("peak_24h_mm")
        cumulative_mm = rainfall_data.get("cumulative_mm", 0)
        forecast_days = rainfall_data.get("forecast_days", 4)

        # Alert on peak 24h severity (IMD-based)
        if peak_severity in (RainfallSeverity.EXTREMELY_HEAVY.value, RainfallSeverity.VERY_HEAVY.value):
            peak_str = f"{peak_mm:.0f}" if peak_mm is not None else "?"
            alerts.append(
                f"IMD Alert: {peak_severity.replace('_', ' ').title()} rainfall "
                f"({peak_str} mm in 24h) expected in the forecast period."
            )
        elif peak_severity == RainfallSeverity.HEAVY.value:
            peak_str = f"{peak_mm:.0f}" if peak_mm is not None else "?"
            alerts.append(
                f"Heavy Rainfall Expected: Peak {peak_str} mm in 24 hours."
            )

        # Alert on waterlogging risk (separate from rainfall severity)
        if waterlogging_risk == WaterloggingRisk.VERY_HIGH.value:
            alerts.append(
                f"Very High Waterlogging Risk: {cumulative_mm:.0f} mm over {forecast_days} days. "
                "Prepare drainage immediately."
            )
        elif waterlogging_risk == WaterloggingRisk.HIGH.value:
            alerts.append(
                f"High Waterlogging Risk: {cumulative_mm:.0f} mm over {forecast_days} days. "
                "Check drainage and protect seedlings."
            )
        elif waterlogging_risk == WaterloggingRisk.MODERATE.value:
            alerts.append(
                f"Moderate Waterlogging Risk: {cumulative_mm:.0f} mm over {forecast_days} days. "
                "Monitor drainage channels."
            )

        # ─── Temperature Alerts (unchanged) ──────────────────────────────
        if max_temp is not None:
            if max_temp > 35:
                alerts.append(f"Heat Advisory: High temperatures up to {max_temp}°C expected.")

        if min_temp is not None:
            if min_temp < 10:
                alerts.append(f"Cold Warning: Temperatures dropping to {min_temp}°C.")

        if not alerts:
            alerts.append("No immediate weather risks detected.")

        return alerts