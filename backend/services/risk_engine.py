import math
from typing import Dict, Any
from backend.models.asteroid import RiskAssessment

def calculate_asteroid_risk(
    diameter_min_meters: float,
    diameter_max_meters: float,
    velocity_km_h: float,
    miss_distance_km: float,
    is_potentially_hazardous: bool
) -> RiskAssessment:
    avg_diameter = (diameter_min_meters + diameter_max_meters) / 2.0
    
    radius_meters = avg_diameter / 2.0
    volume = (4.0 / 3.0) * math.pi * (radius_meters ** 3)
    density_kg_m3 = 3000.0
    mass_kg = volume * density_kg_m3
    
    velocity_m_s = (velocity_km_h * 1000.0) / 3600.0
    
    energy_joules = 0.5 * mass_kg * (velocity_m_s ** 2)
    energy_megatons = energy_joules / 4.184e15
    
    base_factor = 1.2e-7
    if miss_distance_km < 384400:
        distance_factor = 384400 / max(miss_distance_km, 10000.0)
        impact_probability = min(0.015, base_factor * (avg_diameter ** 1.2) * (distance_factor ** 2.2))
    else:
        distance_factor = 384400 / miss_distance_km
        impact_probability = max(1e-9, base_factor * (avg_diameter ** 0.8) * (distance_factor ** 1.5))
        
    if is_potentially_hazardous:
        impact_probability *= 2.5
        
    impact_probability = min(0.05, impact_probability)
    
    diameter_score = min(10.0, max(0.0, math.log10(max(1.0, avg_diameter)) * 3.33 - 1.67))
    proximity_score = min(10.0, max(0.0, 10.0 - (miss_distance_km / 1500000.0)))
    if miss_distance_km < 384400:
        proximity_score = min(10.0, proximity_score + 1.5)
        
    velocity_score = min(10.0, max(0.0, (velocity_km_h - 20000.0) / 13000.0))
    
    hazard_score = (diameter_score * 0.40) + (proximity_score * 0.45) + (velocity_score * 0.15)
    
    if not is_potentially_hazardous:
        hazard_score *= 0.4
        
    hazard_score = round(min(10.0, max(0.0, hazard_score)), 2)
    
    torino_scale = 0
    if impact_probability >= 1e-5:
        if energy_megatons < 1.0:
            torino_scale = 1
        elif energy_megatons < 10.0:
            torino_scale = 2 if impact_probability < 1e-3 else 3
        elif energy_megatons < 100.0:
            torino_scale = 4
        else:
            if impact_probability > 0.01:
                if energy_megatons > 10000.0:
                    torino_scale = 10
                elif energy_megatons > 1000.0:
                    torino_scale = 9
                else:
                    torino_scale = 8
            else:
                torino_scale = 5 if energy_megatons < 1000.0 else (6 if energy_megatons < 10000.0 else 7)
    elif impact_probability >= 1e-7:
        if energy_megatons >= 1.0:
            torino_scale = 1
            
    if torino_scale >= 8:
        danger_level = "CRITICAL"
        description = (
            f"Extremely dangerous collision threat. Torino Scale {torino_scale}. "
            f"Estimated impact energy is {energy_megatons:,.0f} Megatons of TNT (equivalent to "
            f"{energy_megatons/0.015:,.0f} Hiroshima bombs). Collision is certain or highly likely, "
            f"causing major localized or global catastrophe. Immediate agency coordination is required."
        )
    elif torino_scale >= 5:
        danger_level = "HIGH"
        description = (
            f"Serious threat of collision with Torino Scale {torino_scale}. "
            f"Estimated impact energy of {energy_megatons:,.1f} Megatons of TNT. Close monitoring "
            f"and warning system verification are currently active."
        )
    elif torino_scale >= 2 or hazard_score >= 7.0:
        danger_level = "MODERATE"
        description = (
            f"Close encounter classified as moderate risk (Torino Scale {torino_scale}, Hazard Score {hazard_score:.1f}). "
            f"Estimated size is {avg_diameter:.1f}m. While collision probability is low ({impact_probability:.2e}), "
            f"the proximity requires detailed radar tracking and celestial calculations."
        )
    elif is_potentially_hazardous:
        danger_level = "LOW"
        description = (
            f"Classified as potentially hazardous due to proximity ({miss_distance_km/1000000.0:.2f}M km) "
            f"and size ({avg_diameter:.1f}m). Torino Scale {torino_scale}. "
            f"No immediate threat of impact is detected, but orbital perturbation tracking is maintained."
        )
    else:
        danger_level = "MINIMAL"
        description = (
            f"Routine orbital close approach. Estimated diameter is {avg_diameter:.1f}m, passing by at "
            f"{miss_distance_km/1000000.0:.2f}M km with a speed of {velocity_km_h:,.0f} km/h. "
            f"Torino Scale {torino_scale}. Pose no danger to Earth."
        )
        
    return RiskAssessment(
        hazard_score=hazard_score,
        torino_scale=torino_scale,
        impact_probability=impact_probability,
        danger_level=danger_level,
        description=description
    )
