from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from backend.models.asteroid import AsteroidDetail, AsteroidOverview
from backend.services.nasa_client import nasa_client
from backend.cache.redis_cache import cache

router = APIRouter(
    prefix="/api/asteroids",
    tags=["asteroids"]
)

def get_default_dates() -> tuple[str, str]:
    today = datetime.now()
    future_date = today + timedelta(days=6)
    return today.strftime("%Y-%m-%d"), future_date.strftime("%Y-%m-%d")

@router.get("", response_model=Dict[str, List[AsteroidDetail]])
async def get_asteroids(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    bypass_cache: bool = Query(False, description="Force refresh from NASA API")
):
    def_start, def_end = get_default_dates()
    start = start_date or def_start
    end = end_date or def_end
    
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        
        if (end_dt - start_dt).days > 7:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 7 days.")
        if end_dt < start_dt:
            raise HTTPException(status_code=400, detail="End date must be greater than or equal to start date.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    cache_key = f"asteroids:{start}:{end}"
    
    if not bypass_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return {
                date: [AsteroidDetail(**ast) for ast in asts]
                for date, asts in cached_data.items()
            }
            
    data = await nasa_client.get_asteroids(start, end)
    
    serializable_data = {
        date: [ast.model_dump() for ast in asts]
        for date, asts in data.items()
    }
    cache.set(cache_key, serializable_data, expire_seconds=3600)
    
    return data

@router.get("/stats")
async def get_asteroid_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    def_start, def_end = get_default_dates()
    start = start_date or def_start
    end = end_date or def_end
    
    data = await nasa_client.get_asteroids(start, end)
    
    all_asteroids: List[AsteroidDetail] = []
    for ast_list in data.values():
        all_asteroids.extend(ast_list)
        
    total_count = len(all_asteroids)
    if total_count == 0:
        return {
            "total_tracked": 0,
            "hazardous_count": 0,
            "max_hazard_score": 0.0,
            "max_hazard_asteroid": None,
            "average_diameter_meters": 0.0,
            "average_velocity_km_h": 0.0,
            "danger_levels": {"MINIMAL": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
        }
        
    hazardous_count = sum(1 for a in all_asteroids if a.is_potentially_hazardous)
    
    danger_levels = {"MINIMAL": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for a in all_asteroids:
        lvl = a.risk_assessment.danger_level
        danger_levels[lvl] = danger_levels.get(lvl, 0) + 1
        
    max_hazard_ast = max(all_asteroids, key=lambda a: a.risk_assessment.hazard_score)
    
    avg_diameter = sum((a.diameter_min_meters + a.diameter_max_meters)/2.0 for a in all_asteroids) / total_count
    avg_velocity = sum(a.velocity_km_h for a in all_asteroids) / total_count
    
    return {
        "total_tracked": total_count,
        "hazardous_count": hazardous_count,
        "max_hazard_score": max_hazard_ast.risk_assessment.hazard_score,
        "max_hazard_asteroid": max_hazard_ast,
        "average_diameter_meters": round(avg_diameter, 2),
        "average_velocity_km_h": round(avg_velocity, 2),
        "danger_levels": danger_levels
    }

@router.get("/{asteroid_id}", response_model=AsteroidDetail)
async def get_asteroid_by_id(
    asteroid_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    def_start, def_end = get_default_dates()
    start = start_date or def_start
    end = end_date or def_end
    
    data = await nasa_client.get_asteroids(start, end)
    for ast_list in data.values():
        for ast in ast_list:
            if ast.id == asteroid_id:
                return ast
                
    raise HTTPException(status_code=404, detail=f"Asteroid with ID {asteroid_id} not found in date range {start} to {end}.")
