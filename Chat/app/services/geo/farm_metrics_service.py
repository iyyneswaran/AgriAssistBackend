from datetime import datetime, timedelta
from .gee_client import get_gee_client

class FarmMetricsService:
    def __init__(self):
        self.ee = get_gee_client().get_ee()

    def get_metrics(self, latitude: float, longitude: float):
        # Use exact point instead of small buffer. 
        # Tiny buffers on low-res datasets (9000m) can fail to intersect pixel centers.
        geometry = self.ee.Geometry.Point([longitude, latitude])
        
        # 1 & 2. Temperature, Humidity, Soil Moisture (ECMWF ERA5-Land)
        # ERA5-Land provides gap-free global land data (though with ~5-9 day latency)
        # We use a 30-day trailing mean to guarantee we hit recent available observations.
        temp_celsius = None
        humidity_percent = None
        soil_moisture = None
        
        try:
            era5_col = (
                self.ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
                .filterBounds(geometry)
                .filterDate((datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"), 
                            (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"))
                .select(["temperature_2m", "dewpoint_temperature_2m", "volumetric_soil_water_layer_1"])
            )
            
            era5_mean = era5_col.mean()
            era5_stats = era5_mean.reduceRegion(
                reducer=self.ee.Reducer.mean(),
                geometry=geometry,
                scale=9000,
                maxPixels=1e9
            ).getInfo()
            
            if era5_stats:
                t_k = era5_stats.get("temperature_2m")
                td_k = era5_stats.get("dewpoint_temperature_2m")
                vsw = era5_stats.get("volumetric_soil_water_layer_1")
                
                if t_k is not None:
                    temp_celsius = t_k - 273.15
                    
                if t_k is not None and td_k is not None:
                    t_c = t_k - 273.15
                    td_c = td_k - 273.15
                    import math
                    # Magnus-Tetens formula for Relative Humidity
                    e_t = math.exp((17.625 * t_c) / (243.04 + t_c))
                    e_td = math.exp((17.625 * td_c) / (243.04 + td_c))
                    humidity_percent = 100.0 * (e_td / e_t)
                
                if vsw is not None:
                    # vsw is m3/m3 (volumetric). 
                    # Approximate top layer (0-7cm) water in mm = vsw * 70mm
                    soil_moisture = vsw * 70.0

        except Exception as e:
            print(f"Error fetching ERA5 data: {e}")

        # 3. Soil pH (OpenLandMap)
        soil_ph = None
        try:
            # OpenLandMap represents pH as H2O pH * 10
            # b0 = soil depth 0cm
            ph_image = self.ee.Image("OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02").select("b0")
            
            ph_stats = ph_image.reduceRegion(
                reducer=self.ee.Reducer.mean(),
                geometry=geometry,
                scale=250,
                maxPixels=1e9
            ).getInfo()
            
            if ph_stats and ph_stats.get("b0") is not None:
                # b0 value is pH * 10
                soil_ph = ph_stats.get("b0") / 10.0
        except Exception as e:
            print(f"Error fetching pH data: {e}")

        return {
            "temperature_celsius": round(temp_celsius, 1) if temp_celsius is not None else None,
            "humidity_percent": round(humidity_percent, 1) if humidity_percent is not None else None,
            "soil_moisture_mm": round(soil_moisture, 2) if soil_moisture is not None else None,
            "soil_ph": round(soil_ph, 1) if soil_ph is not None else None
        }
