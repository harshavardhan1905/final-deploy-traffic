from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from dotenv import load_dotenv

import requests
import folium
import openrouteservice
import math
import os

app = FastAPI()
load_dotenv()
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup template rendering
templates = Jinja2Templates(directory="templates")

# API Keys from environment variables
# TOMTOM_API_KEY = "eZEcIlVKK9lGUqDzqLtnm8b7xOG1FfFG"
# ORS_API_KEY = "5b3ce3597851110001cf624882ff503deb274a2981515b5272c8cb05"

# if not TOMTOM_API_KEY or not ORS_API_KEY:
#     raise ValueError("API keys not set in environment variables.")

# ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
# TOMTOM_TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")
ORS_API_KEY = os.environ.get("ORS_API_KEY")
# ORS_API_KEY = "5b3ce3597851110001cf624882ff503deb274a2981515b5272c8cb05"
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
TOMTOM_TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
TOMTOM_INCIDENTS_URL = "https://api.tomtom.com/traffic/services/5/incidentDetails"
print("ORS_API_KEY:", ORS_API_KEY)
print("TOMTOM_API_KEY:", TOMTOM_API_KEY)

# Haversine formula for distance calculation
# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371.0
#     lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
#     dlat = lat2_r - lat1_r
#     dlon = lon2_r - lon1_r
#     a = (math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
#     c = 2 * math.asin(math.sqrt(a))
#     return R * c

# Fetch route from OpenRouteService
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

# Fetch traffic data from TomTom
def get_traffic(lat: float, lon: float):
    """Fetch real-time traffic flow data from TomTom."""
    params = {"key": TOMTOM_API_KEY, "point": f"{lat},{lon}"}
    response = requests.get(TOMTOM_TRAFFIC_URL, params=params)
    if response.status_code != 200:
        return None  # Return None if traffic data is unavailable
    print("Sucess fetching traffic")
    return response.json()

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
        return None  # Return None if incidents data is unavailable
    incidents_data = response.json()
    print("Success fetching incidents:", incidents_data)
    return incidents_data

# def get_points_along_route(route_coords, interval=0.01):
#     points = []
#     for i in range(len(route_coords) - 1):
#         lat1, lon1 = route_coords[i]
#         lat2, lon2 = route_coords[i + 1]
#         dist = ((lat2 - lat1)**2 + (lon2 - lon1)**2)**0.5
#         num_points = int(dist / interval)
#         for j in range(num_points):
#             fraction = j / num_points
#             lat = lat1 + (lat2 - lat1) * fraction
#             lon = lon1 + (lon2 - lon1) * fraction
#             points.append((lat, lon))
#     return points

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/map", response_class=HTMLResponse)
def show_map(origin: str, destination: str):
    origin_lon, origin_lat = map(float, origin.split(","))
    destination_lon, destination_lat = map(float, destination.split(","))
    data = fetch_route(origin, destination)
    if "routes" not in data:
        return HTMLResponse("<h1>Error: Route not found</h1>")
    
    client = openrouteservice.Client(key=ORS_API_KEY)
    route_coords = openrouteservice.convert.decode_polyline(data['routes'][0]['geometry'])
    route_coords = [(coord[1], coord[0]) for coord in route_coords['coordinates']]
    
    m = folium.Map(location=route_coords[0], zoom_start=13)
    
    segment_length = max(1, len(route_coords) // 30)
    for i in range(0, len(route_coords) - 1, segment_length):
        mid_index = i + segment_length // 2
        if mid_index >= len(route_coords):
            mid_index = len(route_coords) - 1
        mid_lat, mid_lon = route_coords[mid_index]
        traffic_data = get_traffic(mid_lat, mid_lon)
        color = "blue"
        if traffic_data and "flowSegmentData" in traffic_data:
            speed = traffic_data["flowSegmentData"].get("currentSpeed", 0)
            free_flow_speed = traffic_data["flowSegmentData"].get("freeFlowSpeed", 1)
            congestion_level = speed / free_flow_speed
            if congestion_level > 0.8:
                color = "green"
            elif congestion_level > 0.5:
                color = "yellow"
            else:
                color = "red"
        folium.PolyLine(route_coords[i:i + segment_length + 1], color=color, weight=5, opacity=0.7).add_to(m)
    
    folium.Marker(route_coords[0], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(route_coords[-1], tooltip="End", icon=folium.Icon(color="red")).add_to(m)

    min_lat, min_lon = min(origin_lat, destination_lat), min(origin_lon, destination_lon)
    max_lat, max_lon = max(origin_lat, destination_lat), max(origin_lon, destination_lon)
    incidents_data = get_incidents(min_lat, min_lon, max_lat, max_lon)
    
    print("Traffic API Response:", incidents_data)
    if incidents_data and "incidents" in incidents_data:
        for incident in incidents_data["incidents"]:
            coordinates = incident["geometry"]["coordinates"]
            if isinstance(coordinates[0], list):  # If it's a list of lists (LineString)
                lat, lon = coordinates[0][1], coordinates[0][0]  # Take the first coordinate pair
            else:  # If it's a single coordinate pair
                lat, lon = coordinates[1], coordinates[0]

            description = incident.get("properties", {}).get("description", "No details")
            folium.Marker(
                [lat, lon], 
                tooltip=f"🚨 Incident: {description}", 
                icon=folium.Icon(color="orange", icon="exclamation-triangle", prefix="fa")
            ).add_to(m)
    return m._repr_html_()
