import os
import logging
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from backend.models.asteroid import AsteroidDetail, AsteroidOverview
from backend.services.risk_engine import calculate_asteroid_risk

logger = logging.getLogger("NasaClient")

class NasaClient:
    def __init__(self):
        self.api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.nasa.gov/neo/rest/v1"
        self.timeout = 10.0

    async def get_asteroids(self, start_date: str, end_date: str) -> Dict[str, List[AsteroidDetail]]:
        try:
            if self.api_key == "DEMO_KEY" and not os.getenv("FORCE_NASA_API", "false").lower() == "true":
                logger.info("Using DEMO_KEY, falling back to mock data to prevent rate limits.")
                return self._generate_mock_asteroids(start_date, end_date)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/feed",
                    params={
                        "start_date": start_date,
                        "end_date": end_date,
                        "api_key": self.api_key
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_nasa_response(data)
                elif response.status_code == 429:
                    logger.warning("NASA API rate limit exceeded (429). Falling back to mock data.")
                else:
                    logger.error(f"NASA API returned status code {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Failed to fetch data from NASA API: {e}. Falling back to mock data.")
            
        return self._generate_mock_asteroids(start_date, end_date)

    def _parse_nasa_response(self, data: Dict[str, Any]) -> Dict[str, List[AsteroidDetail]]:
        parsed_data = {}
        neos = data.get("near_earth_objects", {})
        
        for date, asteroid_list in neos.items():
            parsed_data[date] = []
            for ast in asteroid_list:
                try:
                    close_approach = ast.get("close_approach_data", [{}])[0]
                    
                    id_str = ast.get("id", "0")
                    name = ast.get("name", "Unknown Asteroid")
                    
                    dia = ast.get("estimated_diameter", {})
                    dia_min = dia.get("meters", {}).get("estimated_diameter_min", 10.0)
                    dia_max = dia.get("meters", {}).get("estimated_diameter_max", 30.0)
                    
                    is_hazard = ast.get("is_potentially_hazardous_asteroid", False)
                    
                    app_date = close_approach.get("close_approach_date", date)
                    epoch = close_approach.get("epoch_date_close_approach", 0)
                    
                    velocity = float(close_approach.get("relative_velocity", {}).get("kilometers_per_hour", 30000.0))
                    miss_dist = float(close_approach.get("miss_distance", {}).get("kilometers", 5000000.0))
                    orbiting = close_approach.get("orbiting_body", "Earth")
                    
                    risk = calculate_asteroid_risk(
                        diameter_min_meters=dia_min,
                        diameter_max_meters=dia_max,
                        velocity_km_h=velocity,
                        miss_distance_km=miss_dist,
                        is_potentially_hazardous=is_hazard
                    )
                    
                    asteroid_detail = AsteroidDetail(
                        id=id_str,
                        name=name,
                        diameter_min_meters=dia_min,
                        diameter_max_meters=dia_max,
                        is_potentially_hazardous=is_hazard,
                        close_approach_date=app_date,
                        epoch_date_close_approach=epoch,
                        velocity_km_h=velocity,
                        miss_distance_km=miss_dist,
                        orbiting_body=orbiting,
                        risk_assessment=risk
                    )
                    
                    parsed_data[date].append(asteroid_detail)
                except Exception as e:
                    logger.error(f"Error parsing individual asteroid data: {e}")
                    continue
                    
        return parsed_data

    def _generate_mock_asteroids(self, start_date_str: str, end_date_str: str) -> Dict[str, List[AsteroidDetail]]:
        mock_data = {}
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        delta = end_date - start_date
        
        templates = [
            {"id": "99942", "name": "99942 Apophis", "dia_min": 310.0, "dia_max": 370.0, "hazard": True, "vel": 110200.0, "dist": 38000.0},
            {"id": "101955", "name": "101955 Bennu", "dia_min": 490.0, "dia_max": 510.0, "hazard": True, "vel": 101000.0, "dist": 420000.0},
            {"id": "2026AW1", "name": "2026 AW1 (Threat Simulation)", "dia_min": 950.0, "dia_max": 1400.0, "hazard": True, "vel": 135000.0, "dist": 15000.0},
            {"id": "363505", "name": "363505 (2003 UC20)", "dia_min": 1900.0, "dia_max": 4200.0, "hazard": True, "vel": 64800.0, "dist": 8300000.0},
            {"id": "4179", "name": "4179 Toutatis", "dia_min": 2400.0, "dia_max": 5400.0, "hazard": False, "vel": 41200.0, "dist": 12500000.0},
            {"id": "532299", "name": "2013 QK48", "dia_min": 80.0, "dia_max": 180.0, "hazard": True, "vel": 51000.0, "dist": 2100000.0},
            {"id": "504629", "name": "2008 WP76", "dia_min": 15.0, "dia_max": 45.0, "hazard": False, "vel": 28000.0, "dist": 480000.0},
            {"id": "2020QG", "name": "2020 QG (Ultra Close Passing)", "dia_min": 3.0, "dia_max": 6.0, "hazard": False, "vel": 44200.0, "dist": 9300.0},
            {"id": "2026BX", "name": "2026 BX9", "dia_min": 12.0, "dia_max": 27.0, "hazard": False, "vel": 32100.0, "dist": 1400000.0},
            {"id": "162173", "name": "162173 Ryugu", "dia_min": 850.0, "dia_max": 900.0, "hazard": False, "vel": 83000.0, "dist": 9500000.0},
        ]
        
        for i in range(delta.days + 1):
            curr_date = start_date + timedelta(days=i)
            curr_date_str = curr_date.strftime("%Y-%m-%d")
            
            day_asteroids = []
            
            seed = int(curr_date.strftime("%Y%m%d"))
            
            num_asteroids = 2 + (seed % 3)
            
            for j in range(num_asteroids):
                idx = (seed + j * 7) % len(templates)
                tpl = templates[idx]
                
                p_factor = 0.9 + ((seed + j) % 21) * 0.01
                
                dia_min = round(tpl["dia_min"] * p_factor, 1)
                dia_max = round(tpl["dia_max"] * p_factor, 1)
                vel = round(tpl["vel"] * p_factor, 1)
                
                dist = round(tpl["dist"] * (0.8 + ((seed + j * 3) % 41) * 0.01), 1)
                
                if tpl["id"] == "2026AW1":
                    dist = 12000.0 + ((seed + j) % 5000)
                
                risk = calculate_asteroid_risk(
                    diameter_min_meters=dia_min,
                    diameter_max_meters=dia_max,
                    velocity_km_h=vel,
                    miss_distance_km=dist,
                    is_potentially_hazardous=tpl["hazard"]
                )
                
                epoch = int(curr_date.replace(hour=12, minute=0).timestamp() * 1000)
                
                ast = AsteroidDetail(
                    id=f"{tpl['id']}_{curr_date_str.replace('-', '')}",
                    name=tpl["name"],
                    diameter_min_meters=dia_min,
                    diameter_max_meters=dia_max,
                    is_potentially_hazardous=tpl["hazard"],
                    close_approach_date=curr_date_str,
                    epoch_date_close_approach=epoch,
                    velocity_km_h=vel,
                    miss_distance_km=dist,
                    orbiting_body="Earth",
                    risk_assessment=risk
                )
                day_asteroids.append(ast)
                
            mock_data[curr_date_str] = day_asteroids
            
        return mock_data

nasa_client = NasaClient()
