from typing import List, Dict, Optional
from uszipcode import SearchEngine

def validate_zipcode(zipcode: str) -> bool:
    """Validate if a string is a valid US zipcode."""
    search = SearchEngine()
    result = search.by_zipcode(zipcode)
    return result.zipcode is not None

def get_zipcode_info(zipcode: str) -> Optional[Dict]:
    """Get latitude, longitude, and other info for a zipcode using uszipcode."""
    if not validate_zipcode(zipcode):
        raise ValueError(f"Invalid zipcode format: {zipcode}")
    
    search = SearchEngine()
    result = search.by_zipcode(zipcode)
    
    return {
        'zipcode': result.zipcode,
        'lat': result.lat,
        'lng': result.lng,
        'city': result.major_city,
        'state': result.state,
        'county': result.county,
        'population': result.population,
        'median_home_value': result.median_home_value,
        'median_household_income': result.median_household_income
    }

def find_nearby_zipcodes(zipcode: str, radius_miles: float) -> List[str]:
    """Find all zipcodes within a given radius of the target zipcode."""
    search = SearchEngine()
    
    # Get the center zipcode info
    center = search.by_zipcode(zipcode)
    if not center:
        raise ValueError(f"Could not get information for zipcode: {zipcode}")
    
    # Search for zipcodes within radius
    nearby = search.by_coordinates(
        lat=center.lat,
        lng=center.lng,
        radius=radius_miles,
        returns=50  # Limit to 50 results
    )
    
    return [z.zipcode for z in nearby]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles using the Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3959.87433  # Earth's radius in miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return round(distance, 2) 