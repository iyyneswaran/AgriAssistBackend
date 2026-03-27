"""
Advanced Analysis Service — Combines IoT sensor data with GEE regional data
and weather data to produce actionable agricultural insights.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime


class AdvancedAnalysisService:
    """Computes 8 advanced analysis indices from sensor + GEE + weather data."""

    # ─── Thresholds ───
    MOISTURE_LOW = 30.0        # % below which irrigation is needed
    MOISTURE_HIGH = 80.0       # % above which over-irrigation is detected
    HUMIDITY_FUNGAL = 80.0     # % humidity threshold for fungal risk
    HUMIDITY_HIGH = 75.0       # % humidity for disease risk
    HUMIDITY_LOW = 40.0        # % humidity for ET irrigation
    TEMP_HIGH = 35.0           # °C heat stress
    TEMP_DISEASE_MIN = 20.0    # °C lower bound for disease-favorable range
    TEMP_DISEASE_MAX = 30.0    # °C upper bound for disease-favorable range
    TEMP_GROWTH_MIN = 15.0     # °C minimum for ideal growth
    TEMP_GROWTH_MAX = 35.0     # °C maximum for ideal growth
    MOISTURE_GROWTH_MIN = 30.0 # %
    MOISTURE_GROWTH_MAX = 70.0 # %
    HUMIDITY_GROWTH_MIN = 40.0 # %
    HUMIDITY_GROWTH_MAX = 80.0 # %

    def compute_all(
        self,
        sensor_temp: Optional[float],
        sensor_humidity: Optional[float],
        sensor_moisture: Optional[float],
        gee_temp: Optional[float] = None,
        gee_humidity: Optional[float] = None,
        gee_moisture: Optional[float] = None,
        gee_ph: Optional[float] = None,
        weather_temp: Optional[float] = None,
        weather_humidity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Compute all 8 analyses plus pH-based insights."""
        analyses = []

        # 1. Irrigation Need (Low moisture)
        analyses.append(self._irrigation_need(sensor_moisture))

        # 2. Fungal Risk (High humidity)
        analyses.append(self._fungal_risk(sensor_humidity))

        # 3. Evapotranspiration-based Irrigation
        analyses.append(self._et_irrigation(sensor_temp, sensor_humidity))

        # 4. Disease Risk Index (Composite)
        analyses.append(self._disease_risk(sensor_humidity, sensor_temp))

        # 5. Crop Stress Index
        analyses.append(self._crop_stress_index(sensor_temp, sensor_humidity, sensor_moisture))

        # 6. Growth Condition Score
        analyses.append(self._growth_condition(sensor_temp, sensor_humidity, sensor_moisture))

        # 7. Over-Irrigation Detection
        analyses.append(self._over_irrigation(sensor_moisture, sensor_humidity))

        # 8. Micro-Climate vs Weather Comparison
        analyses.append(self._microclimate_comparison(
            sensor_temp, sensor_humidity, sensor_moisture,
            gee_temp, gee_humidity, gee_moisture,
            weather_temp, weather_humidity,
        ))

        # Bonus: pH-based Soil Nutrient Prediction
        if gee_ph is not None:
            analyses.append(self._ph_nutrient_prediction(gee_ph))

        return analyses

    # ─────────────────────────────────────────────
    # 1. Irrigation Need
    # ─────────────────────────────────────────────
    def _irrigation_need(self, moisture: Optional[float]) -> Dict[str, Any]:
        if moisture is None:
            return self._no_data_card("irrigation_need", "Irrigation Need", "irrigation", "💧")

        if moisture < 20:
            severity = "critical"
            summary = f"Soil moisture critically low at {moisture:.0f}%"
            recommendation = "Immediate irrigation required. Soil is severely dry and crop roots may be stressed."
        elif moisture < self.MOISTURE_LOW:
            severity = "high"
            summary = f"Soil moisture is low at {moisture:.0f}%"
            recommendation = "Schedule irrigation within the next few hours to prevent crop stress."
        elif moisture < 50:
            severity = "medium"
            summary = f"Soil moisture is moderate at {moisture:.0f}%"
            recommendation = "Monitor moisture levels. Consider irrigation if levels continue to drop."
        else:
            severity = "low"
            summary = f"Soil moisture is adequate at {moisture:.0f}%"
            recommendation = "No irrigation needed currently. Moisture levels are within optimal range."

        return {
            "id": "irrigation_need",
            "title": "Irrigation Need",
            "category": "irrigation",
            "severity": severity,
            "icon": "💧",
            "summary": summary,
            "recommendation": recommendation,
            "score": max(0, min(100, (100 - moisture))),
            "details": {"moisture_percent": moisture},
        }

    # ─────────────────────────────────────────────
    # 2. Fungal Risk (High Humidity)
    # ─────────────────────────────────────────────
    def _fungal_risk(self, humidity: Optional[float]) -> Dict[str, Any]:
        if humidity is None:
            return self._no_data_card("fungal_risk", "Fungal Disease Risk", "disease", "🍄")

        if humidity > 90:
            severity = "critical"
            summary = f"Very high humidity at {humidity:.0f}% — extreme fungal risk"
            recommendation = "Apply preventive fungicide immediately. Ensure proper air circulation and drainage."
        elif humidity > self.HUMIDITY_FUNGAL:
            severity = "high"
            summary = f"High humidity at {humidity:.0f}% — elevated fungal risk"
            recommendation = "Monitor crops closely for fungal symptoms. Consider preventive fungicide application."
        elif humidity > 65:
            severity = "medium"
            summary = f"Moderate humidity at {humidity:.0f}%"
            recommendation = "Keep monitoring. Fungal risk is moderate but could increase with temperature changes."
        else:
            severity = "low"
            summary = f"Humidity at {humidity:.0f}% — low fungal risk"
            recommendation = "Conditions are unfavorable for fungal growth. No action needed."

        return {
            "id": "fungal_risk",
            "title": "Fungal Disease Risk",
            "category": "disease",
            "severity": severity,
            "icon": "🍄",
            "summary": summary,
            "recommendation": recommendation,
            "score": max(0, min(100, (humidity - 40) * 1.67)) if humidity > 40 else 0,
            "details": {"humidity_percent": humidity},
        }

    # ─────────────────────────────────────────────
    # 3. Evapotranspiration-based Irrigation
    # ─────────────────────────────────────────────
    def _et_irrigation(self, temp: Optional[float], humidity: Optional[float]) -> Dict[str, Any]:
        if temp is None or humidity is None:
            return self._no_data_card("et_irrigation", "Evapotranspiration Irrigation", "irrigation", "🌡️")

        # Simple ET proxy: high temp + low humidity = high water loss
        # Normalize: temp contribution (0-100), inverse humidity contribution (0-100)
        temp_factor = max(0, min(100, (temp - 15) * 5))  # 15°C=0, 35°C=100
        humidity_factor = max(0, min(100, (100 - humidity)))  # 0% humidity = 100, 100% = 0
        et_score = (temp_factor * 0.6 + humidity_factor * 0.4)

        if et_score > 75:
            severity = "critical"
            summary = f"Rapid water loss detected (ET score: {et_score:.0f}/100)"
            recommendation = "Increase irrigation frequency immediately. High temperature ({:.0f}°C) combined with low humidity ({:.0f}%) is causing severe evapotranspiration.".format(temp, humidity)
        elif et_score > 50:
            severity = "high"
            summary = f"Elevated water loss rate (ET score: {et_score:.0f}/100)"
            recommendation = "Consider increasing irrigation frequency. Temperature and humidity conditions are driving significant water loss."
        elif et_score > 30:
            severity = "medium"
            summary = f"Moderate evapotranspiration (ET score: {et_score:.0f}/100)"
            recommendation = "Water loss is moderate. Standard irrigation schedule should be sufficient."
        else:
            severity = "low"
            summary = f"Low evapotranspiration rate (ET score: {et_score:.0f}/100)"
            recommendation = "Water retention is good. Conditions are favorable for minimal water loss."

        return {
            "id": "et_irrigation",
            "title": "Evapotranspiration Irrigation",
            "category": "irrigation",
            "severity": severity,
            "icon": "🌡️",
            "summary": summary,
            "recommendation": recommendation,
            "score": et_score,
            "details": {"temperature": temp, "humidity": humidity, "temp_factor": temp_factor, "humidity_factor": humidity_factor},
        }

    # ─────────────────────────────────────────────
    # 4. Disease Risk Index (Composite)
    # ─────────────────────────────────────────────
    def _disease_risk(self, humidity: Optional[float], temp: Optional[float]) -> Dict[str, Any]:
        if humidity is None or temp is None:
            return self._no_data_card("disease_risk", "Disease Risk Index", "disease", "🦠")

        # Disease thrives: high humidity (>75%) + moderate temp (20-30°C)
        humidity_score = max(0, min(100, (humidity - 50) * 2))  # 50%=0, 100%=100
        # Temp score peaks at 25°C (center of 20-30 range)
        temp_score = max(0, 100 - abs(temp - 25) * 10)  # 25°C=100, 15°C or 35°C=0
        disease_score = humidity_score * 0.6 + temp_score * 0.4

        if disease_score > 70:
            severity = "critical"
            summary = f"High probability of fungal/bacterial disease outbreak in next 24–48 hours"
            recommendation = "Apply preventive treatments immediately. High humidity ({:.0f}%) with disease-favorable temperature ({:.0f}°C) creates ideal conditions for pathogen proliferation.".format(humidity, temp)
        elif disease_score > 45:
            severity = "high"
            summary = f"Elevated disease risk — conditions favor pathogen growth"
            recommendation = "Monitor crops for early disease symptoms. Prepare preventive fungicide/bactericide for application."
        elif disease_score > 25:
            severity = "medium"
            summary = f"Moderate disease risk"
            recommendation = "Routine monitoring recommended. Conditions are partially favorable for disease development."
        else:
            severity = "low"
            summary = f"Low disease risk — conditions unfavorable for pathogens"
            recommendation = "No immediate disease risk. Continue standard crop protection schedule."

        return {
            "id": "disease_risk",
            "title": "Disease Risk Index",
            "category": "disease",
            "severity": severity,
            "icon": "🦠",
            "summary": summary,
            "recommendation": recommendation,
            "score": disease_score,
            "details": {"humidity": humidity, "temperature": temp, "humidity_score": humidity_score, "temp_score": temp_score},
        }

    # ─────────────────────────────────────────────
    # 5. Crop Stress Index
    # ─────────────────────────────────────────────
    def _crop_stress_index(self, temp: Optional[float], humidity: Optional[float], moisture: Optional[float]) -> Dict[str, Any]:
        if temp is None or humidity is None or moisture is None:
            return self._no_data_card("crop_stress", "Crop Stress Index", "stress", "🌾")

        # Stress factors:
        # Temperature: deviation from ideal range (20-30°C)
        temp_stress = 0
        if temp > 40:
            temp_stress = 100
        elif temp > 35:
            temp_stress = 60 + (temp - 35) * 8
        elif temp > 30:
            temp_stress = (temp - 30) * 12
        elif temp < 10:
            temp_stress = (10 - temp) * 10
        elif temp < 15:
            temp_stress = (15 - temp) * 8

        # Moisture: too low or too high is stress
        moisture_stress = 0
        if moisture < 20:
            moisture_stress = (20 - moisture) * 5
        elif moisture < 30:
            moisture_stress = (30 - moisture) * 3
        elif moisture > 85:
            moisture_stress = (moisture - 85) * 5
        elif moisture > 70:
            moisture_stress = (moisture - 70) * 2

        # Humidity extremes
        humidity_stress = 0
        if humidity > 90:
            humidity_stress = (humidity - 90) * 5
        elif humidity < 30:
            humidity_stress = (30 - humidity) * 3

        stress_score = min(100, temp_stress * 0.4 + moisture_stress * 0.35 + humidity_stress * 0.25)

        if stress_score > 70:
            severity = "critical"
            level = "High"
            summary = f"Crop Stress Index: HIGH ({stress_score:.0f}/100) — Immediate action required"
            recommendation = "Crops are under severe stress. Take immediate corrective action: adjust irrigation, provide shade if possible, and monitor closely."
        elif stress_score > 40:
            severity = "high"
            level = "Medium"
            summary = f"Crop Stress Index: MEDIUM ({stress_score:.0f}/100) — Monitor closely"
            recommendation = "Crops are experiencing moderate stress. Monitor conditions and prepare to intervene if stress increases."
        elif stress_score > 20:
            severity = "medium"
            level = "Low-Medium"
            summary = f"Crop Stress Index: LOW-MEDIUM ({stress_score:.0f}/100)"
            recommendation = "Minor stress detected. Continue monitoring — no immediate action needed."
        else:
            severity = "low"
            level = "Healthy"
            summary = f"Crop Stress Index: HEALTHY ({stress_score:.0f}/100)"
            recommendation = "Crops are in excellent condition with minimal stress. Maintain current management practices."

        return {
            "id": "crop_stress",
            "title": "Crop Stress Index",
            "category": "stress",
            "severity": severity,
            "icon": "🌾",
            "summary": summary,
            "recommendation": recommendation,
            "score": stress_score,
            "details": {
                "level": level,
                "temp_stress": round(temp_stress, 1),
                "moisture_stress": round(moisture_stress, 1),
                "humidity_stress": round(humidity_stress, 1),
            },
        }

    # ─────────────────────────────────────────────
    # 6. Growth Condition Score
    # ─────────────────────────────────────────────
    def _growth_condition(self, temp: Optional[float], humidity: Optional[float], moisture: Optional[float]) -> Dict[str, Any]:
        if temp is None or humidity is None or moisture is None:
            return self._no_data_card("growth_condition", "Growth Condition Score", "growth", "🌱")

        issues = []
        score = 100

        # Temperature check
        if temp > self.TEMP_GROWTH_MAX:
            issues.append(f"Too hot ({temp:.0f}°C) ❌")
            score -= min(40, (temp - self.TEMP_GROWTH_MAX) * 8)
        elif temp < self.TEMP_GROWTH_MIN:
            issues.append(f"Too cold ({temp:.0f}°C) ❌")
            score -= min(40, (self.TEMP_GROWTH_MIN - temp) * 8)
        else:
            issues.append(f"Temperature optimal ({temp:.0f}°C) ✅")

        # Moisture check
        if moisture < self.MOISTURE_GROWTH_MIN:
            issues.append(f"Too dry ({moisture:.0f}%) ❌")
            score -= min(35, (self.MOISTURE_GROWTH_MIN - moisture) * 3)
        elif moisture > self.MOISTURE_GROWTH_MAX:
            issues.append(f"Too wet ({moisture:.0f}%) ❌")
            score -= min(25, (moisture - self.MOISTURE_GROWTH_MAX) * 2)
        else:
            issues.append(f"Moisture balanced ({moisture:.0f}%) ✅")

        # Humidity check
        if humidity > self.HUMIDITY_GROWTH_MAX:
            issues.append(f"Humidity too high ({humidity:.0f}%) ❌")
            score -= min(25, (humidity - self.HUMIDITY_GROWTH_MAX) * 2)
        elif humidity < self.HUMIDITY_GROWTH_MIN:
            issues.append(f"Humidity too low ({humidity:.0f}%) ❌")
            score -= min(25, (self.HUMIDITY_GROWTH_MIN - humidity) * 2)
        else:
            issues.append(f"Humidity balanced ({humidity:.0f}%) ✅")

        score = max(0, score)
        check_marks = sum(1 for i in issues if "✅" in i)

        if score >= 80:
            severity = "low"
            summary = "Conditions are ideal for crop growth ✅"
            recommendation = "All growth parameters are within optimal ranges. Maintain current conditions."
        elif score >= 55:
            severity = "medium"
            summary = "Conditions are partially favorable for crop growth"
            recommendation = "Some parameters are outside ideal ranges. Address the issues flagged to optimize growth."
        elif score >= 30:
            severity = "high"
            summary = "Conditions are suboptimal for crop growth"
            recommendation = "Multiple growth conditions are unfavorable. Take corrective measures to improve crop environment."
        else:
            severity = "critical"
            summary = "Current conditions are critical for crop growth ❌"
            recommendation = "Growth conditions are severely compromised. Immediate intervention required to prevent crop damage."

        return {
            "id": "growth_condition",
            "title": "Growth Condition Score",
            "category": "growth",
            "severity": severity,
            "icon": "🌱",
            "summary": summary,
            "recommendation": recommendation,
            "score": score,
            "details": {"conditions": issues, "checks_passed": check_marks, "total_checks": 3},
        }

    # ─────────────────────────────────────────────
    # 7. Over-Irrigation Detection
    # ─────────────────────────────────────────────
    def _over_irrigation(self, moisture: Optional[float], humidity: Optional[float]) -> Dict[str, Any]:
        if moisture is None or humidity is None:
            return self._no_data_card("over_irrigation", "Over-Irrigation Detection", "detection", "🚿")

        if moisture > 85 and humidity > 85:
            severity = "critical"
            summary = f"Over-irrigation detected — risk of root rot"
            recommendation = "Stop irrigation immediately. High moisture ({:.0f}%) combined with high humidity ({:.0f}%) creates waterlogged conditions that cause root rot and suffocation.".format(moisture, humidity)
        elif moisture > self.MOISTURE_HIGH and humidity > self.HUMIDITY_FUNGAL:
            severity = "high"
            summary = f"Possible over-irrigation detected"
            recommendation = "Reduce irrigation frequency. Soil moisture ({:.0f}%) and humidity ({:.0f}%) are both elevated, risking root health.".format(moisture, humidity)
        elif moisture > self.MOISTURE_HIGH or (moisture > 65 and humidity > 80):
            severity = "medium"
            summary = f"Moisture levels are on the higher side"
            recommendation = "Monitor soil moisture carefully. Consider reducing next irrigation cycle slightly."
        else:
            severity = "low"
            summary = f"No over-irrigation detected"
            recommendation = "Irrigation levels appear appropriate. Soil moisture and humidity are within normal ranges."

        # Score: higher = worse (more over-irrigated)
        overwater_score = max(0, min(100, ((moisture - 50) * 1.2 + max(0, humidity - 60) * 0.8)))

        return {
            "id": "over_irrigation",
            "title": "Over-Irrigation Detection",
            "category": "detection",
            "severity": severity,
            "icon": "🚿",
            "summary": summary,
            "recommendation": recommendation,
            "score": overwater_score,
            "details": {"moisture_percent": moisture, "humidity_percent": humidity},
        }

    # ─────────────────────────────────────────────
    # 8. Micro-Climate vs Weather Comparison
    # ─────────────────────────────────────────────
    def _microclimate_comparison(
        self,
        sensor_temp: Optional[float],
        sensor_humidity: Optional[float],
        sensor_moisture: Optional[float],
        gee_temp: Optional[float],
        gee_humidity: Optional[float],
        gee_moisture: Optional[float],
        weather_temp: Optional[float] = None,
        weather_humidity: Optional[float] = None,
    ) -> Dict[str, Any]:
        # Use weather data first, fall back to GEE regional data
        regional_temp = weather_temp if weather_temp is not None else gee_temp
        regional_humidity = weather_humidity if weather_humidity is not None else gee_humidity

        if sensor_temp is None or regional_temp is None:
            return self._no_data_card("microclimate", "Micro-Climate Comparison", "climate", "🌍")

        temp_diff = sensor_temp - regional_temp
        humidity_diff = (sensor_humidity - regional_humidity) if (sensor_humidity is not None and regional_humidity is not None) else None

        # Build comparison details
        comparisons = []
        comparisons.append({
            "metric": "Temperature",
            "field_value": f"{sensor_temp:.1f}°C",
            "regional_value": f"{regional_temp:.1f}°C",
            "difference": f"{temp_diff:+.1f}°C",
        })
        if humidity_diff is not None:
            comparisons.append({
                "metric": "Humidity",
                "field_value": f"{sensor_humidity:.0f}%",
                "regional_value": f"{regional_humidity:.0f}%",
                "difference": f"{humidity_diff:+.0f}%",
            })
        if sensor_moisture is not None and gee_moisture is not None:
            moisture_diff = sensor_moisture - gee_moisture
            comparisons.append({
                "metric": "Soil Moisture",
                "field_value": f"{sensor_moisture:.0f}%",
                "regional_value": f"{gee_moisture:.1f}mm",
                "difference": f"Δ {moisture_diff:+.1f}",
            })

        abs_temp_diff = abs(temp_diff)
        if abs_temp_diff > 5:
            severity = "high"
            direction = "higher" if temp_diff > 0 else "lower"
            summary = f"Field temperature is {abs_temp_diff:.1f}°C {direction} than regional average"
            recommendation = f"Significant micro-climate deviation detected. Your field is notably {direction} than the surrounding region, which may affect crop management decisions."
        elif abs_temp_diff > 2:
            severity = "medium"
            direction = "higher" if temp_diff > 0 else "lower"
            summary = f"Field temperature is {abs_temp_diff:.1f}°C {direction} than regional average"
            recommendation = "Moderate micro-climate difference. Consider this when planning pesticide/fertilizer applications."
        else:
            severity = "low"
            summary = f"Field conditions closely match regional weather (Δ{temp_diff:+.1f}°C)"
            recommendation = "Your field's micro-climate is consistent with regional conditions. Standard regional advisories apply."

        return {
            "id": "microclimate",
            "title": "Micro-Climate vs Weather",
            "category": "climate",
            "severity": severity,
            "icon": "🌍",
            "summary": summary,
            "recommendation": recommendation,
            "score": min(100, abs_temp_diff * 15),
            "details": {"comparisons": comparisons, "temp_diff": temp_diff},
        }

    # ─────────────────────────────────────────────
    # Bonus: pH-based Soil Nutrient Prediction
    # ─────────────────────────────────────────────
    def _ph_nutrient_prediction(self, ph: float) -> Dict[str, Any]:
        if ph < 5.5:
            severity = "critical"
            summary = f"Strongly Acidic (pH {ph:.1f}) — High toxicity and deficiency risks"
            recommendation = "Apply lime to raise pH. Soil may lack N, P, K, Ca, Mg, S. Possible deficiencies include stunted growth and leaf discoloration (e.g., Phosphorus deficiency). Toxic levels of Aluminum and Manganese likely. Limit acidifying fertilizers."
            nutrients_status = "Available (Low): N, P, K, Ca, Mg, S | Toxic: Al, Mn"
            score = 80
        elif ph <= 6.5:
            severity = "medium"
            summary = f"Moderately Acidic (pH {ph:.1f}) — Excellent nutrient availability"
            recommendation = "Maintain current practices. Monitor for slight Calcium or Magnesium needs for specific sensitive crops."
            nutrients_status = "Available: N, P, K, Ca, Mg, S, Fe, Mn | Locked: None"
            score = 30
        elif ph <= 7.5:
            severity = "low"
            summary = f"Neutral (pH {ph:.1f}) — Ideal for major nutrients"
            recommendation = "Maintain balanced fertilization. No major amendments required; nutrient availability is stable."
            nutrients_status = "Available: N, P, K, Ca, Mg, S | Locked: None"
            score = 10
        else:
            severity = "high"
            summary = f"Alkaline (pH {ph:.1f}) — Risk of micronutrient lockout"
            recommendation = "Apply elemental sulfur or acidifying fertilizers to lower pH. Foliar micronutrient sprays needed to prevent Fe, Mn, Zn, Cu, B deficiencies (e.g., interveinal chlorosis or stunted growth)."
            nutrients_status = "Available (Lowered): N, P, K | Locked: Fe, Mn, Zn, Cu, B"
            score = 65

        return {
            "id": "ph_nutrients",
            "title": "Soil pH & Nutrient Status",
            "category": "growth",
            "severity": severity,
            "icon": "⚗️",
            "summary": summary,
            "recommendation": recommendation,
            "score": score,
            "details": {"ph": ph, "nutrients_status": nutrients_status},
        }

    # ─────────────────────────────────────────────
    # Helper: No-data placeholder
    # ─────────────────────────────────────────────
    def _no_data_card(self, id: str, title: str, category: str, icon: str) -> Dict[str, Any]:
        return {
            "id": id,
            "title": title,
            "category": category,
            "severity": "low",
            "icon": icon,
            "summary": "Insufficient sensor data for analysis",
            "recommendation": "Connect your IoT sensors to start receiving real-time analysis and predictions.",
            "score": None,
            "details": None,
        }
