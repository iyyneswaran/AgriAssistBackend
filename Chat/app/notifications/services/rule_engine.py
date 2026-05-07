"""
Rule Engine
============
Deterministic rule-based logic that evaluates FarmContext against predefined
agricultural rules to produce structured RuleResult decisions.

AI is NOT used here — all decisions are deterministic.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.notifications.schemas.event_schemas import FarmContext

logger = logging.getLogger(__name__)


@dataclass
class RuleResult:
    """Output of a single rule evaluation."""
    triggered: bool = False
    event_type: str = ""
    severity: str = "low"
    confidence: int = 0
    situation: str = ""
    impact: str = ""
    recommended_action: str = ""
    source_signals: dict = field(default_factory=dict)


class RuleEngine:
    """Evaluates 6 deterministic agricultural notification rules."""

    # ─── Thresholds ───
    MOISTURE_LOW = 30.0
    MOISTURE_CRITICAL = 15.0
    MOISTURE_HIGH = 80.0
    HUMIDITY_FUNGAL = 80.0
    TEMP_DISEASE_MIN = 20.0
    TEMP_DISEASE_MAX = 30.0
    RAIN_POSTPONE = 50.0
    NDVI_STRESS = 0.3
    FLOOD_RAIN_MM = 50.0
    FLOOD_SAT = 85.0
    SENSOR_OFFLINE_MIN = 15

    def evaluate_all(self, ctx: FarmContext) -> list[RuleResult]:
        """Run all rules, return only triggered results."""
        rules = [
            self._smart_irrigation,
            self._disease_warning,
            self._drought_intelligence,
            self._flood_prevention,
            self._resource_optimization,
            self._iot_offline,
        ]
        results = []
        for fn in rules:
            try:
                r = fn(ctx)
                if r.triggered:
                    results.append(r)
            except Exception as e:
                logger.error(f"Rule error {fn.__name__}: {e}")
        return results

    # ───────── Rule 1: Smart Irrigation ─────────
    def _smart_irrigation(self, ctx: FarmContext) -> RuleResult:
        r = RuleResult(event_type="smart_irrigation")
        moisture = ctx.sensor_moisture
        rain_prob = ctx.weather_rain_probability
        forecast_rain = ctx.weather_forecast_rain_mm

        if moisture is None:
            return r

        # Rain coming + soil OK → postpone
        if rain_prob and rain_prob >= self.RAIN_POSTPONE and moisture >= self.MOISTURE_LOW:
            water_saved = max(80, int((forecast_rain or 0) * 8))
            r.triggered = True
            r.severity = "medium"
            r.confidence = min(95, int(rain_prob))
            r.situation = (
                f"Rain expected with {rain_prob:.0f}% probability while soil "
                f"moisture is at {moisture:.0f}%, sufficient for current needs."
            )
            r.impact = (
                f"Irrigation can be postponed, saving approximately "
                f"{water_saved}L of water. Rainfall will supplement soil moisture."
            )
            r.recommended_action = (
                "Postpone scheduled irrigation. Resume only if soil moisture "
                "drops below 30% after the rainfall."
            )
            r.source_signals = {
                "soil_moisture": moisture, "rain_probability": rain_prob,
                "forecast_rain_mm": forecast_rain, "water_saved_l": water_saved,
            }
            return r

        # Critical dryness
        if moisture < self.MOISTURE_CRITICAL:
            r.triggered = True
            r.severity = "critical"
            r.confidence = 90
            no_rain = rain_prob is None or rain_prob < 20
            r.situation = (
                f"Soil moisture critically low at {moisture:.0f}%. "
                + ("No rain expected." if no_rain else f"Rain probability only {rain_prob:.0f}%.")
            )
            r.impact = "Immediate risk of wilting and irreversible yield loss."
            r.recommended_action = (
                "Start irrigation immediately. Apply deep watering to restore "
                "moisture above 40%."
            )
            r.source_signals = {"soil_moisture": moisture, "rain_probability": rain_prob}
            return r

        # Moderately low
        if moisture < self.MOISTURE_LOW:
            r.triggered = True
            r.severity = "high"
            r.confidence = 80
            r.situation = f"Soil moisture low at {moisture:.0f}%, nearing stress threshold."
            r.impact = "Early water stress signs may appear within hours."
            r.recommended_action = "Schedule irrigation within 2-4 hours."
            r.source_signals = {"soil_moisture": moisture}
            return r

        return r

    # ───────── Rule 2: Disease Warning ─────────
    def _disease_warning(self, ctx: FarmContext) -> RuleResult:
        r = RuleResult(event_type="disease_warning")
        humidity = ctx.sensor_humidity or ctx.weather_humidity
        temp = ctx.sensor_temperature or ctx.weather_temperature

        if humidity is None or temp is None:
            return r

        # Camera-detected disease → critical
        if ctx.disease_detected and ctx.disease_confidence and ctx.disease_confidence > 50:
            r.triggered = True
            r.severity = "critical"
            r.confidence = int(ctx.disease_confidence)
            r.situation = (
                f"Disease detected: {ctx.disease_type or 'Unknown'} "
                f"({ctx.disease_confidence:.0f}% confidence) from camera analysis."
            )
            r.impact = "Can spread rapidly to neighboring plants."
            r.recommended_action = (
                "Isolate affected plants. Apply targeted treatment within 24 hours."
            )
            r.source_signals = {
                "disease_type": ctx.disease_type,
                "disease_confidence": ctx.disease_confidence,
                "humidity": humidity, "temperature": temp,
            }
            return r

        # Environmental conditions
        in_range = self.TEMP_DISEASE_MIN <= temp <= self.TEMP_DISEASE_MAX
        high_hum = humidity >= self.HUMIDITY_FUNGAL

        if high_hum and in_range:
            r.triggered = True
            r.severity = "high"
            r.confidence = min(90, 60 + int((humidity - self.HUMIDITY_FUNGAL) * 1.5))
            r.situation = (
                f"High fungal risk: humidity {humidity:.0f}% and temperature "
                f"{temp:.0f}°C (disease-favorable range)."
            )
            r.impact = "Disease outbreak probability increases in 24-48 hours."
            r.recommended_action = (
                "Apply preventive fungicide within 24 hours. Improve air circulation."
            )
            r.source_signals = {"humidity": humidity, "temperature": temp}
            return r

        if high_hum:
            r.triggered = True
            r.severity = "medium"
            r.confidence = 55
            r.situation = f"Elevated humidity at {humidity:.0f}% promotes fungal growth."
            r.impact = "Moderate risk of fungal development on leaf surfaces."
            r.recommended_action = "Monitor crops for disease symptoms."
            r.source_signals = {"humidity": humidity, "temperature": temp}

        return r

    # ───────── Rule 3: Drought Intelligence ─────────
    def _drought_intelligence(self, ctx: FarmContext) -> RuleResult:
        r = RuleResult(event_type="drought_intelligence")
        moisture = ctx.sensor_moisture
        if moisture is None:
            return r

        signals = 0
        details: dict = {}

        if moisture < self.MOISTURE_LOW:
            signals += 1
            details["low_moisture"] = moisture
        if ctx.gee_ndvi is not None and ctx.gee_ndvi < self.NDVI_STRESS:
            signals += 1
            details["low_ndvi"] = ctx.gee_ndvi
        if ctx.weather_forecast_rain_mm is not None and ctx.weather_forecast_rain_mm < 2:
            signals += 1
            details["dry_forecast_mm"] = ctx.weather_forecast_rain_mm
        temp = ctx.sensor_temperature or ctx.weather_temperature
        if temp is not None and temp > 35:
            signals += 1
            details["high_temp"] = temp

        if signals >= 3:
            r.triggered = True
            r.severity = "critical"
            r.confidence = min(95, 60 + signals * 10)
            r.situation = (
                f"Multiple drought indicators: moisture {moisture:.0f}%, "
                + (f"NDVI {ctx.gee_ndvi:.2f}, " if ctx.gee_ndvi and ctx.gee_ndvi < self.NDVI_STRESS else "")
                + "minimal rainfall forecast."
            )
            r.impact = "Yield reduction of 15-25% possible without intervention."
            r.recommended_action = (
                "Increase irrigation frequency by 15-20%. Apply mulching."
            )
            r.source_signals = details
        elif signals >= 2:
            r.triggered = True
            r.severity = "high"
            r.confidence = 65
            r.situation = f"Early drought signs: soil moisture {moisture:.0f}%."
            r.impact = "Stress will intensify within 48-72 hours if unchecked."
            r.recommended_action = "Plan increased irrigation. Monitor closely."
            r.source_signals = details

        return r

    # ───────── Rule 4: Flood Prevention ─────────
    def _flood_prevention(self, ctx: FarmContext) -> RuleResult:
        r = RuleResult(event_type="flood_prevention")
        rain = ctx.weather_forecast_rain_mm
        moisture = ctx.sensor_moisture
        elevation = ctx.gee_elevation
        rain_prob = ctx.weather_rain_probability

        if rain is None and rain_prob is None:
            return r

        risk = 0
        if rain and rain >= self.FLOOD_RAIN_MM:
            risk += 40
        if moisture and moisture >= self.FLOOD_SAT:
            risk += 30
        if elevation is not None and elevation < 50:
            risk += 15
        if rain_prob and rain_prob >= 80:
            risk += 15

        if risk >= 55:
            r.triggered = True
            r.severity = "critical"
            r.confidence = min(90, risk + 10)
            r.situation = (
                f"Flood risk high. "
                + (f"Heavy rainfall {rain:.0f}mm forecast. " if rain and rain >= self.FLOOD_RAIN_MM else "")
                + (f"Soil saturated at {moisture:.0f}%. " if moisture and moisture >= self.FLOOD_SAT else "")
            )
            r.impact = "Waterlogging damages roots and washes away fertilizers."
            r.recommended_action = (
                "Open drainage channels immediately. Stop all irrigation."
            )
            r.source_signals = {
                "forecast_rain_mm": rain, "soil_moisture": moisture,
                "elevation": elevation, "flood_risk_score": risk,
            }
        elif risk >= 30:
            r.triggered = True
            r.severity = "high"
            r.confidence = 60
            r.situation = f"Moderate flood risk. Rainfall {rain or 0:.0f}mm expected."
            r.impact = "Prolonged wet conditions may cause waterlogging."
            r.recommended_action = "Inspect drainage. Skip next irrigation cycle."
            r.source_signals = {"forecast_rain_mm": rain, "soil_moisture": moisture}

        return r

    # ───────── Rule 5: Resource Optimization ─────────
    def _resource_optimization(self, ctx: FarmContext) -> RuleResult:
        r = RuleResult(event_type="resource_optimization")
        temp = ctx.sensor_temperature or ctx.weather_temperature
        humidity = ctx.sensor_humidity or ctx.weather_humidity
        wind = ctx.weather_wind_speed

        if temp is None or humidity is None:
            return r

        hour = datetime.utcnow().hour
        high_evap = temp > 30 and humidity < 50
        windy = wind is not None and wind > 15

        if high_evap and 6 <= hour <= 14:
            loss = 20 + (10 if windy else 0)
            r.triggered = True
            r.severity = "medium"
            r.confidence = 75
            r.situation = (
                f"High evaporation: {temp:.0f}°C, {humidity:.0f}% humidity"
                + (f", wind {wind:.0f} km/h" if windy else "")
                + ". Irrigating now wastes water."
            )
            r.impact = f"~{loss}% irrigation water lost to evaporation."
            r.recommended_action = (
                "Postpone irrigation to evening (after 6 PM) or early morning."
            )
            r.source_signals = {
                "temperature": temp, "humidity": humidity,
                "wind_speed": wind, "efficiency_loss_pct": loss,
            }

        return r

    # ───────── Rule 6: IoT System Offline ─────────
    def _iot_offline(self, ctx: FarmContext) -> RuleResult:
        r = RuleResult(event_type="iot_offline")

        if ctx.sensor_last_seen is None:
            if ctx.sensor_temperature is None and ctx.sensor_humidity is None:
                r.triggered = True
                r.severity = "medium"
                r.confidence = 70
                r.situation = "IoT sensors not responding. No recent data."
                r.impact = "Automated recommendations are less accurate."
                r.recommended_action = "Check sensor power and Wi-Fi connectivity."
                r.source_signals = {"sensor_last_seen": None}
            return r

        mins_off = (datetime.utcnow() - ctx.sensor_last_seen).total_seconds() / 60

        if mins_off >= self.SENSOR_OFFLINE_MIN:
            r.triggered = True
            r.severity = "high" if mins_off >= 30 else "medium"
            r.confidence = min(95, 60 + int(mins_off))
            r.situation = (
                f"Sensor offline for {mins_off:.0f} minutes "
                f"(last: {ctx.sensor_last_seen.strftime('%H:%M')})."
            )
            r.impact = "Real-time monitoring interrupted."
            r.recommended_action = "Check ESP32 power, Wi-Fi, and MQTT broker."
            r.source_signals = {
                "last_seen": ctx.sensor_last_seen.isoformat(),
                "minutes_offline": round(mins_off, 1),
            }

        return r
