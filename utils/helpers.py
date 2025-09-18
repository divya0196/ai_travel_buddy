import math
from typing import List, Tuple, Optional
from geopy.distance import geodesic
from models.data_models import Location, Attraction

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate distance between two geographical points in kilometers"""
    try:
        return geodesic(point1, point2).kilometers
    except Exception:
        # Fallback to haversine formula
        return haversine_distance(point1, point2)

def haversine_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate distance using haversine formula"""
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def optimize_route(locations: List[Location], start_location: Optional[Location] = None) -> List[Attraction]:
    """Simple route optimization using nearest neighbor algorithm"""
    
    if not locations:
        return []
        
    if len(locations) == 1:
        # Convert Location to mock Attraction for consistency
        return [location_to_attraction(locations[0])]
    
    # Start from the given start location or first location
    if start_location:
        current = start_location
        remaining = locations.copy()
    else:
        current = locations[0]
        remaining = locations[1:]
    
    optimized_route = []
    
    # Add starting location as attraction
    optimized_route.append(location_to_attraction(current))
    
    # Greedy nearest neighbor
    while remaining:
        current_coords = (current.latitude, current.longitude)
        
        # Find nearest unvisited location
        nearest_location = None
        min_distance = float('inf')
        
        for location in remaining:
            location_coords = (location.latitude, location.longitude)
            distance = calculate_distance(current_coords, location_coords)
            
            if distance < min_distance:
                min_distance = distance
                nearest_location = location
        
        if nearest_location:
            optimized_route.append(location_to_attraction(nearest_location))
            remaining.remove(nearest_location)
            current = nearest_location
    
    return optimized_route

def location_to_attraction(location: Location) -> Attraction:
    """Convert Location to Attraction for route optimization"""
    return Attraction(
        id=f"loc_{hash(location.name)}",
        name=location.name,
        description=f"Visit {location.name}",
        location=location,
        category="location",
        rating=4.0,
        price=0,
        opening_hours={
            "monday": "00:00-23:59",
            "tuesday": "00:00-23:59",
            "wednesday": "00:00-23:59",
            "thursday": "00:00-23:59",
            "friday": "00:00-23:59",
            "saturday": "00:00-23:59",
            "sunday": "00:00-23:59"
        },
        visit_duration=90,
        popularity_score=0.5
    )

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:.2f}"

def format_time_duration(minutes: int) -> str:
    """Format time duration in minutes to human readable format"""
    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes < 1440:  # Less than a day
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours}h {remaining_minutes}m"
    else:
        days = minutes // 1440
        remaining_hours = (minutes % 1440) // 60
        if remaining_hours == 0:
            return f"{days} day{'s' if days > 1 else ''}"
        else:
            return f"{days}d {remaining_hours}h"

def calculate_budget_utilization(spent: float, budget: float) -> dict:
    """Calculate budget utilization metrics"""
    if budget == 0:
        return {
            "utilization_percentage": 0,
            "remaining_budget": 0,
            "status": "no_budget"
        }
    
    utilization = (spent / budget) * 100
    remaining = budget - spent
    
    if utilization <= 80:
        status = "under_budget"
    elif utilization <= 100:
        status = "on_budget"
    else:
        status = "over_budget"
    
    return {
        "utilization_percentage": round(utilization, 2),
        "remaining_budget": round(remaining, 2),
        "status": status
    }

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate geographical coordinates"""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180

def get_time_zone_offset(location: str) -> int:
    """Get timezone offset for location (simplified)"""
    # This is a simplified implementation
    # In production, use a proper timezone library
    timezone_offsets = {
        "paris": 1,
        "london": 0,
        "tokyo": 9,
        "new york": -5,
        "los angeles": -8,
        "sydney": 10
    }
    
    return timezone_offsets.get(location.lower(), 0)
