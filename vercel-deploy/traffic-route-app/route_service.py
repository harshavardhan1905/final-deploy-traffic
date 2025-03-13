from fastapi import HTTPException
import requests
import math
from datetime import datetime, timedelta

# API configurations
TOMTOM_API_KEY = "eZEcIlVKK9lGUqDzqLtnm8b7xOG1FfFG"
ORS_API_KEY = "5b3ce3597851110001cf624882ff503deb274a2981515b5272c8cb05"
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
TOMTOM_TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
TOMTOM_INCIDENTS_URL = "https://api.tomtom.com/traffic/services/5/incidentDetails"

def fetch_route(origin: str, destination: str):
    """Fetch route data from ORS API."""
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    try:
        origin_lon, origin_lat = map(float, origin.split(","))
        destination_lon, destination_lat = map(float, destination.split(","))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid coordinate format. Use 'longitude,latitude'.")
    
    location_data = {
        "coordinates": [[origin_lon, origin_lat], [destination_lon, destination_lat]],
        "geometry": "true"
    }
    response = requests.post(ORS_URL, json=location_data, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"ORS API Error: {response.text}")
    data = response.json()
    if "routes" not in data or not data["routes"]:
        raise HTTPException(status_code=404, detail="No route found. Check if the locations are reachable.")
    print("success fetching route")
    return data

def get_traffic(lat: float, lon: float):
    """Fetch real-time traffic flow data with improved error handling."""
    try:
        params = {"key": TOMTOM_API_KEY, "point": f"{lat},{lon}"}
        response = requests.get(TOMTOM_TRAFFIC_URL, params=params, timeout=5)
        response.raise_for_status()
        print("fetching traffic")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Traffic API Error: {e}")
        return None

def get_incidents(min_lat: float, min_lon: float, max_lat: float, max_lon: float):
    """Fetch real-time traffic incidents from TomTom with debugging."""
    params = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "key": TOMTOM_API_KEY
    }
    response = requests.get(TOMTOM_INCIDENTS_URL, params=params)
    print("Traffic API Response Status Code:", response.status_code)
    if response.status_code != 200:
        print("Traffic API Error Response:", response.text)
        return None
    incidents_data = response.json()
    print("Success fetching incidents:", incidents_data)
    return incidents_data

def calculate_eta(route_coords: list, traffic_data_list: list) -> dict:
    """Calculate ETA based on route segments and traffic conditions."""
    total_distance = 0
    total_time = 0
    
    for i in range(len(route_coords) - 1):
        # Calculate distance between consecutive coordinates (in km)
        lat1, lon1 = route_coords[i]
        lat2, lon2 = route_coords[i + 1]
        
        # Using haversine formula for distance calculation
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        segment_distance = R * c
        
        total_distance += segment_distance
        
        # Get traffic speed for this segment
        traffic_data = traffic_data_list[i] if i < len(traffic_data_list) else None
        if traffic_data and "flowSegmentData" in traffic_data:
            speed = traffic_data["flowSegmentData"].get("currentSpeed", 60)  # Default 60 km/h
        else:
            speed = 40  # Default speed if no traffic data
            
        # Calculate time for this segment (hours)
        segment_time = segment_distance / speed
        total_time += segment_time
    
    # Convert total time to minutes
    total_minutes = total_time * 60
    
    # Calculate arrival time
    current_time = datetime.now()
    arrival_time = current_time + timedelta(minutes=total_minutes)
    
    return {
        "total_time_minutes": round(total_minutes, 2),
        "arrival_time": arrival_time.strftime("%H:%M"),
        "total_distance_km": round(total_distance, 2)
    }