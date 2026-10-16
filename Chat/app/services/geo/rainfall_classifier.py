"""
Rainfall classification based on India Meteorological Department (IMD) standards.

IMD 24-hour rainfall thresholds (mm):
  - No Rain:           < 2.5
  - Light:           2.5 – 15.5
  - Moderate:       15.6 – 64.4
  - Heavy:          64.5 – 115.5
  - Very Heavy:    115.6 – 204.4
  - Extremely Heavy: ≥ 204.5

Reference: IMD Terminology for Quantitative Rainfall Forecasts.

IMPORTANT: These thresholds apply ONLY to 24-hour accumulated rainfall.
A 4-day cumulative total MUST NOT be classified using 24-hour thresholds.
"""

from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field, asdict


# ─── IMD Severity Enum ───────────────────────────────────────────────────
class RainfallSeverity(str, Enum):
    NO_RAIN = "no_rain"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    VERY_HEAVY = "very_heavy"
    EXTREMELY_HEAVY = "extremely_heavy"
    UNKNOWN = "unknown"  # when data is missing


class WaterloggingRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class RiverFloodStatus(str, Enum):
    NOT_ASSESSED = "not_assessed"
    # We do NOT have a validated flood model, so this is the only honest value.


# ─── IMD 24-hour thresholds (mm) ─────────────────────────────────────────
_IMD_24H_THRESHOLDS = [
    (204.5, RainfallSeverity.EXTREMELY_HEAVY),
    (115.6, RainfallSeverity.VERY_HEAVY),
    (64.5,  RainfallSeverity.HEAVY),
    (15.6,  RainfallSeverity.MODERATE),
    (2.5,   RainfallSeverity.LIGHT),
    (0.0,   RainfallSeverity.NO_RAIN),
]


def classify_24h_rainfall(rainfall_mm: Optional[float]) -> RainfallSeverity:
    """Classify 24-hour accumulated rainfall using IMD thresholds."""
    if rainfall_mm is None:
        return RainfallSeverity.UNKNOWN
    for threshold, severity in _IMD_24H_THRESHOLDS:
        if rainfall_mm >= threshold:
            return severity
    return RainfallSeverity.NO_RAIN


# ─── Multi-day cumulative severity (heuristic, NOT IMD standard) ─────────
# These are agricultural impact heuristics, clearly labelled as such.
# They answer: "Given this many mm spread over N days, how concerned
# should a farmer be about waterlogging?"

_CUMULATIVE_WATERLOGGING_THRESHOLDS = {
    # (days): [(mm_threshold, risk), ...]
    4: [
        (300.0, WaterloggingRisk.VERY_HIGH),
        (200.0, WaterloggingRisk.HIGH),
        (100.0, WaterloggingRisk.MODERATE),
        (0.0,   WaterloggingRisk.LOW),
    ],
}


def assess_waterlogging_risk(
    cumulative_mm: Optional[float],
    forecast_days: int = 4,
    soil_moisture_mm: Optional[float] = None,
) -> WaterloggingRisk:
    """
    Assess agricultural waterlogging risk from cumulative rainfall.
    
    This is a rule-based heuristic, NOT a calibrated flood model.
    It considers total rainfall over the forecast period and, optionally,
    current soil moisture.
    
    Args:
        cumulative_mm: Total forecast rainfall in mm over the period.
        forecast_days: Number of days the rainfall is spread over.
        soil_moisture_mm: Current soil moisture in mm (from ERA5, if available).
    
    Returns:
        WaterloggingRisk enum value.
    """
    if cumulative_mm is None:
        return WaterloggingRisk.UNKNOWN

    thresholds = _CUMULATIVE_WATERLOGGING_THRESHOLDS.get(forecast_days)
    if thresholds is None:
        # Fallback: scale 4-day thresholds linearly
        scale = forecast_days / 4.0
        thresholds = [
            (t * scale, risk)
            for t, risk in _CUMULATIVE_WATERLOGGING_THRESHOLDS[4]
        ]

    base_risk = WaterloggingRisk.LOW
    for threshold, risk in thresholds:
        if cumulative_mm >= threshold:
            base_risk = risk
            break

    # If soil is already saturated, bump up risk by one level
    if soil_moisture_mm is not None and soil_moisture_mm > 50.0:
        risk_order = [
            WaterloggingRisk.LOW,
            WaterloggingRisk.MODERATE,
            WaterloggingRisk.HIGH,
            WaterloggingRisk.VERY_HIGH,
        ]
        idx = risk_order.index(base_risk)
        if idx < len(risk_order) - 1:
            base_risk = risk_order[idx + 1]

    return base_risk


# ─── Result dataclass ────────────────────────────────────────────────────
@dataclass
class DailyRainfall:
    day: int                       # 1-indexed
    rainfall_mm: float
    severity: str                  # RainfallSeverity value


@dataclass
class RainfallClassification:
    """Complete rainfall assessment returned by the backend."""
    cumulative_mm: float
    forecast_days: int
    daily_breakdown: List[DailyRainfall] = field(default_factory=list)
    peak_24h_mm: Optional[float] = None
    peak_24h_severity: str = RainfallSeverity.UNKNOWN.value
    waterlogging_risk: str = WaterloggingRisk.UNKNOWN.value
    river_flood_status: str = RiverFloodStatus.NOT_ASSESSED.value
    classification_method: str = "imd_24h_thresholds"
    disclaimer: str = (
        "Waterlogging risk is a rule-based estimate for agricultural planning. "
        "It is NOT a calibrated flood probability. "
        "River flood risk is not assessed — consult CWC/IMD flood bulletins."
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def build_classification(
    cumulative_mm: Optional[float],
    forecast_days: int,
    daily_totals: Optional[List[float]] = None,
    soil_moisture_mm: Optional[float] = None,
) -> RainfallClassification:
    """
    Build a complete rainfall classification from forecast data.
    
    Args:
        cumulative_mm: Total forecast rainfall in mm.
        forecast_days: Number of days covered.
        daily_totals: Optional list of daily rainfall totals (mm per day).
        soil_moisture_mm: Optional current soil moisture for waterlogging.
    
    Returns:
        RainfallClassification with all fields populated.
    """
    if cumulative_mm is None:
        return RainfallClassification(
            cumulative_mm=0.0,
            forecast_days=forecast_days,
            peak_24h_severity=RainfallSeverity.UNKNOWN.value,
            waterlogging_risk=WaterloggingRisk.UNKNOWN.value,
        )

    # Build daily breakdown
    daily_breakdown = []
    peak_24h = 0.0

    if daily_totals:
        for i, mm in enumerate(daily_totals):
            severity = classify_24h_rainfall(mm)
            daily_breakdown.append(DailyRainfall(
                day=i + 1,
                rainfall_mm=round(mm, 2),
                severity=severity.value,
            ))
            if mm > peak_24h:
                peak_24h = mm
    else:
        # No daily breakdown available — estimate average daily
        avg_daily = cumulative_mm / forecast_days if forecast_days > 0 else 0
        for i in range(forecast_days):
            severity = classify_24h_rainfall(avg_daily)
            daily_breakdown.append(DailyRainfall(
                day=i + 1,
                rainfall_mm=round(avg_daily, 2),
                severity=severity.value,
            ))
        peak_24h = avg_daily

    peak_severity = classify_24h_rainfall(peak_24h)
    waterlogging = assess_waterlogging_risk(cumulative_mm, forecast_days, soil_moisture_mm)

    return RainfallClassification(
        cumulative_mm=round(cumulative_mm, 2),
        forecast_days=forecast_days,
        daily_breakdown=daily_breakdown,
        peak_24h_mm=round(peak_24h, 2),
        peak_24h_severity=peak_severity.value,
        waterlogging_risk=waterlogging.value,
        river_flood_status=RiverFloodStatus.NOT_ASSESSED.value,
    )
