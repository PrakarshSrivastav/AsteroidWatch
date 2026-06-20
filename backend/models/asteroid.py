from pydantic import BaseModel, Field
from typing import Optional, List

class AsteroidBase(BaseModel):
    id: str = Field(..., description="Unique NASA NEO reference ID")
    name: str = Field(..., description="Name of the asteroid")
    diameter_min_meters: float = Field(..., description="Minimum estimated diameter in meters")
    diameter_max_meters: float = Field(..., description="Maximum estimated diameter in meters")
    is_potentially_hazardous: bool = Field(..., description="NASA classification of hazard potential")
    close_approach_date: str = Field(..., description="Formatted approach date (YYYY-MM-DD)")
    epoch_date_close_approach: int = Field(..., description="Epoch date of close approach in ms")
    velocity_km_h: float = Field(..., description="Velocity in kilometers per hour")
    miss_distance_km: float = Field(..., description="Miss distance in kilometers")
    orbiting_body: str = Field("Earth", description="Orbited celestial body")

class RiskAssessment(BaseModel):
    hazard_score: float = Field(..., description="Physics-based risk score on a 0-10 scale")
    torino_scale: int = Field(..., description="Torino Scale hazard rating (0-10)")
    impact_probability: float = Field(..., description="Estimated probability of collision (0.0 to 1.0)")
    danger_level: str = Field(..., description="Qualitative danger assessment (LOW, MODERATE, HIGH, CRITICAL)")
    description: str = Field(..., description="Human-readable safety summary and analysis")

class AsteroidDetail(AsteroidBase):
    risk_assessment: RiskAssessment = Field(..., description="Custom calculated collision risk analysis")

class AsteroidOverview(BaseModel):
    date: str
    count: int
    asteroids: List[AsteroidDetail]
