# Google Earth Engine (GEE) in AgriAssist — Architecture & Implementation

This document provides a comprehensive end-to-end technical explanation of how **Google Earth Engine (GEE)** is integrated and utilized across the entire `AgriAssist_Prod` application. It details satellite data ingestion, backend services, geospatial analytics, sensor fusion, API endpoints, and frontend user interfaces.

---

## 1. Executive Summary & Purpose

In **AgriAssist**, Google Earth Engine functions as the satellite remote sensing and macro-environmental backbone of the platform. While on-field IoT hardware (ESP32 sensors) provides real-time hyper-local micro-climate measurements (soil moisture, temperature, air humidity), satellite data from Google Earth Engine provides:
1. **Vegetation Health & Biomass Monitoring**: Near-real-time NDVI (Normalized Difference Vegetation Index) derived from Sentinel-2 optical multispectral imagery.
2. **Forecast Precipitation**: Global Forecast System (GFS) 4-day cumulative rainfall predictions.
3. **Forecast Extreme Temperatures**: GFS 4-day diurnal maximum and minimum temperature projections.
4. **Regional Macro-Climate Metrics**: ECMWF ERA5-Land reanalysis for baseline ambient temperature, relative humidity (via the Magnus-Tetens equation), and volumetric root-zone soil water.
5. **Soil Chemical Properties**: OpenLandMap global soil datasets for topsoil pH level (0 cm depth).
6. **Disaster Risk Modeling**: Automated predictive scoring for flash floods, agricultural drought, heat stress, and fungal pathogen proliferation.

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Farmer_Client ["Frontend (React / TypeScript)"]
        LandContext["AppDataContext.tsx\n(Caches Land Coordinates)"]
        ForecastPage["Forecast.tsx\n(Satellite Dashboard & Risk Radar)"]
        FarmDetailsPage["FarmDetails.tsx\n(Field & Crop Dashboard)"]
        AdvAnalysisComp["AdvancedAnalysis.tsx\n(Client-side 6-Factor Analytical Engine)"]
        GeoService["geoService.ts\n(API Client to FastAPI)"]
    end

    subgraph Node_Express ["Express Server (Port 5000)"]
        ExpressRoutes["routes.ts\n(/governance/land)"]
        PrismaDB[("PostgreSQL / Prisma\nStores Land Lat/Lng & Corners")]
    end

    subgraph FastAPI_Backend ["Python Chat & Geo Backend (Port 8001)"]
        GeoRouter["app/api/http/geo.py\n(POST /geo/analyze)"]
        SensorRouter["app/api/http/sensor.py\n(GET /api/sensor-data/analysis/:userId)"]
        GeoSchemas["app/schemas/geo.py\n(GeoAnalyzeRequest / Response)"]
        GeoAnalysisSvc["app/services/geo/geo_analysis_service.py\n(Aggregator & Alert Generator)"]
        
        subgraph Geo_Subservices ["Geo Domain Services"]
            NDVISvc["ndvi_service.py\n(Sentinel-2 SR)"]
            RainfallSvc["rainfall_service.py\n(NOAA GFS0P25)"]
            TempSvc["temperature_service.py\n(NOAA GFS0P25)"]
            FarmMetricsSvc["farm_metrics_service.py\n(ERA5-Land & OpenLandMap)"]
        end

        AdvancedAnalysisSvc["app/services/analysis/analysis_service.py\n(8-Index Sensor + GEE Fusion Engine)"]
        GEEClient["app/services/geo/gee_client.py\n(Client Singleton)"]
        GEEAuth["app/integrations/google/gee_auth.py\n(Service Account Auth & ee.Initialize)"]
    end

    subgraph Google_Cloud ["Google Earth Engine Cloud Platform"]
        S2_Harmonized[("COPERNICUS/S2_SR_HARMONIZED\nSentinel-2 MSI (10m)")]
        NOAA_GFS[("NOAA/GFS0P25\nGlobal Forecast System (27.75km)")]
        ECMWF_ERA5[("ECMWF/ERA5_LAND/HOURLY\nReanalysis (9km)")]
        OpenLandMap_pH[("OpenLandMap/SOL/SOL_PH-H2O\nSoil pH (250m)")]
    end

    %% Data Flow
    ExpressRoutes <--> PrismaDB
    LandContext -->|1. Fetch farm coordinates| ExpressRoutes
    LandContext -->|2. Request satellite analysis| GeoService
    GeoService -->|POST /geo/analyze| GeoRouter
    GeoRouter --> GeoAnalysisSvc
    GeoAnalysisSvc --> NDVISvc & RainfallSvc & TempSvc & FarmMetricsSvc
    NDVISvc & RainfallSvc & TempSvc & FarmMetricsSvc --> GEEClient
    GEEClient --> GEEAuth
    GEEAuth -->|ee.Initialize(credentials)| Google_Cloud

    NDVISvc <--> S2_Harmonized
    RainfallSvc <--> NOAA_GFS
    TempSvc <--> NOAA_GFS
    FarmMetricsSvc <--> ECMWF_ERA5
    FarmMetricsSvc <--> OpenLandMap_pH

    GeoAnalysisSvc -->|GeoAnalyzeResponse JSON| GeoRouter
    GeoRouter -->|GeoAnalysisData| GeoService
    GeoService -->|Update State| LandContext
    LandContext --> ForecastPage
    LandContext --> FarmDetailsPage
    FarmDetailsPage --> AdvAnalysisComp

    SensorRouter --> FarmMetricsSvc
    SensorRouter --> AdvancedAnalysisSvc
```

---

## 3. Earth Engine Datasets & Scientific Algorithms

The application queries four distinct satellite collections from Google Earth Engine. Each has specific temporal filters, spatial reducers, and physical unit conversions:

| Metric / Objective | Earth Engine Image Collection | Spatial Resolution | Temporal Window | Bands Used | Reduction & Transformation Method |
|---|---|---|---|---|---|
| **Vegetation Health (NDVI)** | `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 Surface Reflectance) | 10 meters | Past 30 days | `B8` (NIR: 842 nm), `B4` (Red: 665 nm) | 1. Filter clouds (`CLOUDY_PIXEL_PERCENTAGE < 20`)<br>2. Temporal `median()` composite<br>3. `normalizedDifference(["B8", "B4"])`<br>4. 100m point buffer reduction: `ee.Reducer.mean()` |
| **Cumulative Precipitation Forecast** | `NOAA/GFS0P25` (Global Forecast System) | 0.25° (~27.75 km) | Next 4 days (model run < 24h) | `precipitation_rate` | 1. Filter model runs within last 24h<br>2. Filter `forecast_time` range (now to +4d)<br>3. Temporal `sum()` of rain rates<br>4. Multiply `precipitation_rate` (kg/m²/s) by 10,800s (3-hour intervals) to yield depth in **mm**<br>5. 1000m point buffer reduction: `ee.Reducer.mean()` (scale=5000) |
| **Diurnal Max/Min Temperature** | `NOAA/GFS0P25` | 0.25° (~27.75 km) | Next 4 days (model run < 24h) | `temperature_2m_above_ground` | 1. Filter model runs < 24h and forecast interval<br>2. Absolute peak: `collection.max()`<br>3. Absolute nadir: `collection.min()`<br>4. 1000m buffer reduction: `ee.Reducer.mean()` (scale=5000) |
| **Ambient Temperature & Relative Humidity** | `ECMWF/ERA5_LAND/HOURLY` (ERA5-Land Reanalysis) | ~9 km (0.1°) | 30-day trailing mean | `temperature_2m`, `dewpoint_temperature_2m` | 1. 30-day temporal `mean()`<br>2. Convert Kelvin to Celsius: $T_c = T_k - 273.15$, $T_{dc} = T_{dk} - 273.15$<br>3. Derive Relative Humidity via **Magnus-Tetens Formula**:<br>$$e(T) = \exp\left(\frac{17.625 \cdot T_c}{243.04 + T_c}\right)$$<br>$$e(T_d) = \exp\left(\frac{17.625 \cdot T_{dc}}{243.04 + T_{dc}}\right)$$<br>$$\text{RH} = 100 \cdot \frac{e(T_d)}{e(T)}$$ |
| **Root-zone Soil Moisture** | `ECMWF/ERA5_LAND/HOURLY` | ~9 km (0.1°) | 30-day trailing mean | `volumetric_soil_water_layer_1` | Volumetric fraction ($m^3/m^3$) in top layer (0–7 cm). Converted to water column depth in mm: $\text{Moisture (mm)} = \text{vsw} \times 70.0\text{ mm}$ |
| **Topsoil pH** | `OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02` | 250 meters | Static global baseline | `b0` (0 cm depth) | OpenLandMap encodes soil pH in water as $\text{pH} \times 10$. Converted by dividing by $10.0$: $\text{Soil pH} = b_0 / 10.0$ |

---

## 4. Backend Implementation Details

### 4.1 Authentication & Singleton Client (`app/integrations/google/gee_auth.py` & `app/services/geo/gee_client.py`)

- **Credential Resolution**: `GEEAuth._initialize()` supports three credential injection patterns to ensure zero downtime across local and cloud environments:
  1. `GEE_CREDENTIALS_JSON`: Raw JSON string of the Google Cloud service account key.
  2. `GEE_CREDENTIALS_B64`: Base64-encoded service account key (useful for Railway / Render multi-line environment variable injection).
  3. `GOOGLE_APPLICATION_CREDENTIALS`: File path on the local filesystem (e.g. `app/credentials/service_account.json`).
- **Initialization**: Authenticates using `ee.ServiceAccountCredentials(service_account_email, key_data)` and initializes the runtime via `ee.Initialize(credentials)`.
- **Caching**: `@lru_cache()` on `get_gee()` and `get_gee_client()` ensures the authentication handshake and API socket are created only once across multiple worker threads, eliminating re-authentication overhead.

### 4.2 Satellite Subservices (`app/services/geo/`)

#### 1. `ndvi_service.py`
Calculates vegetation vitality:
```python
geometry = self.ee.Geometry.Point([longitude, latitude]).buffer(100)
collection = (
    self.ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(geometry)
    .filterDate(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    .filter(self.ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
)
ndvi = collection.median().normalizedDifference(["B8", "B4"]).rename("NDVI")
```
- **Health Classification**:
  - $\text{NDVI} < 0.2$: **Poor** (Barren, fallow, water-stressed, or diseased canopy).
  - $0.2 \le \text{NDVI} < 0.5$: **Moderate** (Emerging crops, moderate canopy density).
  - $\text{NDVI} \ge 0.5$: **Healthy** (Dense, vigorous photosynthetic canopy).

#### 2. `rainfall_service.py`
Filters `NOAA/GFS0P25` for recent model runs within 24 hours, aggregates future 3-hour precipitation rates over 4 days, and scales by 10,800 seconds to produce forecast rainfall in millimeters (`forecast_rainfall_mm`).

#### 3. `temperature_service.py`
Applies `collection.max()` and `collection.min()` over the 4-day forecast window of `NOAA/GFS0P25` to return `max_temp_celsius` and `min_temp_celsius`.

#### 4. `farm_metrics_service.py`
Queries `ECMWF/ERA5_LAND/HOURLY` over an exact `ee.Geometry.Point` without small buffer to avoid sampling boundary artifacts on 9 km grid cells.
- Evaluates 30-day trailing mean to bridge ERA5-Land's operational publishing latency (typically 5–9 days).
- Employs Magnus-Tetens formula for relative humidity percentage.
- Computes top 0–7 cm soil moisture depth in mm ($vsw \times 70\text{ mm}$).
- Extracts soil pH from `OpenLandMap` ($b_0 / 10.0$).

#### 5. `geo_analysis_service.py`
Aggregates all 4 subservice outputs into a single payload and evaluates deterministic weather hazard rules:
- **Flood Risk**: `forecast_rainfall_mm > 50` $\to$ `"High Flood Risk: Heavy rainfall expected."`
- **Rain Warning**: `forecast_rainfall_mm > 20` $\to$ `"Moderate Rain Expected."`
- **Heat Advisory**: `max_temp_celsius > 35` $\to$ `"Heat Advisory: High temperatures up to {max_temp}°C expected."`
- **Cold Warning**: `min_temp_celsius < 10` $\to$ `"Cold Warning: Temperatures dropping to {min_temp}°C."`

### 4.3 Pydantic Schemas (`app/schemas/geo.py`)

Defines contract interfaces:
- `GeoAnalyzeRequest`: `{ farmer_id?: string, latitude: float, longitude: float }`
- `GeoAnalyzeResponse`:
  ```json
  {
    "ndvi": { "ndvi_mean": 0.642, "health_status": "Healthy", "date_range_days": 30 },
    "rainfall_forecast": { "forecast_rainfall_mm": 12.4, "forecast_days": 4 },
    "temperature_forecast": { "max_temp_celsius": 34.2, "min_temp_celsius": 22.8, "forecast_days": 4 },
    "farm_metrics": { "temperature_celsius": 29.5, "humidity_percent": 68.2, "soil_moisture_mm": 24.5, "soil_ph": 6.8 },
    "alerts": ["No immediate weather risks detected."]
  }
  ```

### 4.4 API Routers

1. **`app/api/http/geo.py`**:
   - Route: `POST /geo/analyze`
   - Handles client input validation, lazy-loads `GeoAnalysisService`, and manages explicit error statuses (`503 Service Unavailable` for missing credentials or GEE downtime, `500 Internal Error` for computation failures).
2. **`app/api/http/sensor.py`**:
   - Route: `GET /api/sensor-data/analysis/{user_id}`
   - Combines live IoT hardware data (ESP32 via ngrok tunnel or database), regional macro-data from `FarmMetricsService` (`gee_temp`, `gee_humidity`, `gee_moisture`, `gee_ph`), and Open-Meteo weather forecasts.

---

## 5. Advanced Agricultural Analysis Engine (`app/services/analysis/analysis_service.py`)

`AdvancedAnalysisService` combines satellite macro-data with physical sensor measurements across 8 core indices:

1. **Irrigation Need**: Evaluates root-zone moisture depletion ($<20\%$ critical, $<30\%$ high, $<50\%$ moderate).
2. **Fungal Disease Risk**: Monitored when humidity exceeds 75%–90%, conditions where spores germinate rapidly.
3. **Evapotranspiration-based Irrigation (ET Proxy)**: Evaluates atmospheric vapor demand using temperature and inverse humidity:
   $$\text{ET Score} = 0.6 \cdot (\text{Temp Factor}) + 0.4 \cdot (100 - \text{Humidity})$$
4. **Disease Risk Index (Composite)**: Combines temperature favorability (peaking at 25°C) with elevated humidity ($>75\%$) to calculate 24–48 hour pathogen outbreak probabilities.
5. **Crop Stress Index**: Weighted composite penalizing temperature extremes ($>35^\circ\text{C}$ or $<15^\circ\text{C}$), moisture extremes ($<30\%$ or $>70\%$), and humidity extremes.
6. **Growth Condition Score**: Optimal agronomical envelope scoring: Temperature (15–35°C), Soil Moisture (30–70%), Air Humidity (40–80%).
7. **Over-Irrigation & Root Rot Detection**: Detects saturation ($>85\%$ moisture accompanied by $>85\%$ humidity) that starves root systems of oxygen.
8. **Micro-Climate vs Regional Weather Comparison**: Compares field sensor temperature/humidity against GEE regional and Open-Meteo macro-data. Quantifies canopy micro-climate offsets ($\Delta T = T_{\text{sensor}} - T_{\text{GEE}}$).
9. **Soil pH & Nutrient Status (GEE Derived)**:
   - $\text{pH} < 5.5$: Strongly Acidic $\to$ Aluminum/Manganese toxicity risk; N, P, K, Ca, Mg deficiency. Recommends agricultural lime.
   - $5.5 \le \text{pH} \le 6.5$: Moderately Acidic $\to$ Optimal nutrient uptake.
   - $6.5 < \text{pH} \le 7.5$: Neutral $\to$ Ideal availability for all primary macronutrients.
   - $\text{pH} > 7.5$: Alkaline $\to$ Micronutrient lockout (Fe, Mn, Zn, Cu, B chlorosis risk). Recommends elemental sulfur or acidifying fertilizers.

---

## 6. Server & Route Gateway (`Backend/server/src/routes/routes.ts`)

The Node.js Express server acts as the custodian of farmer identity and geographic coordinates:
- **`POST /governance/land` (`registerLand`)**: Validates and stores the farmer's field location (GPS `latitude`, `longitude`, parcel corners, soil type, and acreage) in PostgreSQL via Prisma.
- **`GET /governance/land` (`getMyLand`)**: Supplies authenticated land metadata to the client application.
- **Coordinate Hand-off**: The frontend retrieves the farmer's registered parcel latitude and longitude from Express and forwards them to the Python FastAPI `/geo/analyze` endpoint. This separation ensures the Python geospatial backend remains stateless and focused solely on analytical computation.

---

## 7. Frontend Integration & User Experience

### 7.1 Geo Service Client (`frontend/src/services/geoService.ts`)

- Exposes `analyzeGeo(latitude, longitude, farmerId?)`.
- Dispatches HTTP `POST` requests to `VITE_CHAT_API_URL/geo/analyze`.
- Exports TypeScript interfaces: `NDVIData`, `RainfallData`, `TemperatureData`, `FarmMetricsData`, and `GeoAnalysisData`.

### 7.2 State & Cache Management (`frontend/src/context/AppDataContext.tsx`)

- Invokes `fetchGeoData()` automatically upon user authentication once the land coordinates are loaded from `getMyLand()`.
- Stores `geoData`, `geoLoading`, and `geoError` in global application context.
- Exposes `refreshGeo()` for user-triggered on-demand refresh without page reload.

### 7.3 Satellite Dashboard & Disaster Radar (`frontend/src/pages/Forecast.tsx`)

The Forecast screen translates raw GEE arrays into actionable visual components:
1. **Satellite Metric Cards**:
   - **Circular SVG NDVI Gauge**: Displays the mean NDVI value with an animated SVG radial stroke color-coded to health status (`#4ade80` for Healthy, `#facc15` for Moderate, `#f87171` for Poor).
   - **4-Day Rainfall Card**: Displays cumulative rainfall in millimeters with a blue weather indicator.
   - **Temperature Extremes Card**: Shows projected diurnal maximum (orange) and minimum (blue) temperatures.
2. **Disaster Risk Assessment Meters**:
   - **Flood Risk**: Computed via piecewise linear interpolation from forecast rainfall:
     $$80\text{ mm} \to 95\%, \quad 50\text{ mm} \to 75\%, \quad 20\text{ mm} \to 45\%, \quad 5\text{ mm} \to 20\%$$
   - **Drought Risk**: Multi-factor metric combining rainfall deficit with satellite vegetation stress:
     - Rainfall contribution: $<2\text{ mm} \to +50\%$, $<10\text{ mm} \to +30\%$, $<20\text{ mm} \to +10\%$.
     - Satellite NDVI penalty: $\text{NDVI} < 0.2 \to +40\%$, $\text{NDVI} < 0.4 \to +20\%$.
   - **Heat Stress**: Evaluated from projected peak temperature ($>45^\circ\text{C} \to 95\%$, $>40^\circ\text{C} \to 75\%$, $>35^\circ\text{C} \to 55\%$).
3. **Expandable Dynamic Alert Banners**:
   - If any disaster risk crosses $\ge 40\%$ (Moderate) or $\ge 70\%$ (High), expandable warning cards appear with specific mitigation advice (e.g. checking drainage trenches, setting up shade nets, adjusting irrigation cycles).

### 7.4 Farm Details & Advanced Analysis (`frontend/src/pages/FarmDetails.tsx` & `frontend/src/components/farm/AdvancedAnalysis.tsx`)

- `FarmDetails.tsx` extracts `geoData.farm_metrics` (`temperature_celsius`, `humidity_percent`, `soil_moisture_mm`, `soil_ph`) and passes them into `<AdvancedAnalysis />`.
- `AdvancedAnalysis.tsx` runs an in-browser analytical calculation mirroring the Python backend, supporting full internationalization (`useTranslation()` with Tamil, Hindi, English, etc.) and collapsible severity cards:
  - **Irrigation Need Card** (💧)
  - **Fungal Disease Risk Card** (🦠)
  - **Evapotranspiration Irrigation Card** (🌡️)
  - **Crop Stress Index Card** (🌾)
  - **Growth Condition Score Card** (🌱)
  - **Soil pH & Nutrient Status Card** (🧪)

---

## 8. Configuration & Environment Reference

To run Google Earth Engine in `Backend/Chat/.env`, configure:

```dotenv
# Path to service account private key JSON file (local development)
GOOGLE_APPLICATION_CREDENTIALS=app/credentials/service_account.json

# Service account client email registered in Google Cloud Project
GEE_SERVICE_ACCOUNT=agriassist@agriassist-488113.iam.gserviceaccount.com

# OPTIONAL: Inline JSON string (useful for cloud platforms like Railway/Render)
# GEE_CREDENTIALS_JSON={"type": "service_account", "project_id": ...}

# OPTIONAL: Base64-encoded credentials string (alternative cloud deployment)
# GEE_CREDENTIALS_B64=eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjog...
```

### Verification Checklist
1. Ensure the Google Cloud project has the **Earth Engine API** enabled.
2. Confirm the service account `GEE_SERVICE_ACCOUNT` is registered in the Earth Engine Cloud Console as an authorized user.
3. Test connectivity by sending a POST request to `http://localhost:8001/geo/analyze`:
   ```json
   {
     "latitude": 11.0168,
     "longitude": 76.9558
   }
   ```
   A successful response returns all four geospatial domains (`ndvi`, `rainfall_forecast`, `temperature_forecast`, `farm_metrics`) and calculated `alerts`.
