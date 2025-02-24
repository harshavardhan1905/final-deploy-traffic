from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import requests
import folium
import openrouteservice
import math
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup template rendering
templates = Jinja2Templates(directory="templates")

# API Keys from environment variables
TOMTOM_API_KEY = "eZEcIlVKK9lGUqDzqLtnm8b7xOG1FfFG"
ORS_API_KEY = "5b3ce3597851110001cf624882ff503deb274a2981515b5272c8cb05"

if not TOMTOM_API_KEY or not ORS_API_KEY:
    raise ValueError("API keys not set in environment variables.")

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
TOMTOM_TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

# Haversine formula for distance calculation
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = (math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Fetch route from OpenRouteService
def fetch_route(origin: str, destination: str):
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    try:
        origin_lon, origin_lat = map(float, origin.split(","))
        destination_lon, destination_lat = map(float, destination.split(","))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid coordinate format. Use 'longitude,latitude'.")

    location_data = {
        "coordinates": [[origin_lon, origin_lat], [destination_lon, destination_lat]],
        "geometry": True
    }

    response = requests.post(ORS_URL, json=location_data, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"ORS API Error: {response.text}")

    data = response.json()
    if "routes" not in data or not data["routes"]:
        raise HTTPException(status_code=404, detail="No route found. Check if the locations are reachable.")

    return data

# Fetch traffic data from TomTom
def get_traffic(lat: float, lon: float):
    params = {"key": TOMTOM_API_KEY, "point": f"{lat},{lon}"}
    try:
        response = requests.get(TOMTOM_TRAFFIC_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching traffic data: {e}")
        return None

def get_points_along_route(route_coords, interval=0.01):
    points = []
    for i in range(len(route_coords) - 1):
        lat1, lon1 = route_coords[i]
        lat2, lon2 = route_coords[i + 1]
        dist = ((lat2 - lat1)**2 + (lon2 - lon1)**2)**0.5
        num_points = int(dist / interval)
        for j in range(num_points):
            fraction = j / num_points
            lat = lat1 + (lat2 - lat1) * fraction
            lon = lon1 + (lon2 - lon1) * fraction
            points.append((lat, lon))
    return points

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/map", response_class=HTMLResponse)
def show_map(origin: str, destination: str):
    data = fetch_route(origin, destination)
    route_coords = openrouteservice.convert.decode_polyline(data["routes"][0]["geometry"])
    route_coords = [(coord[1], coord[0]) for coord in route_coords["coordinates"]]

    lats = [coord[0] for coord in route_coords]
    lons = [coord[1] for coord in route_coords]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    points_to_check = get_points_along_route(route_coords)
    traffic_data_points = {}
    for point in points_to_check:
        traffic_data = get_traffic(point[0], point[1])
        if traffic_data and "flowSegmentData" in traffic_data:
            traffic_data_points[point] = traffic_data["flowSegmentData"]["frc"]

    for i in range(len(route_coords) - 1):
        lat1, lon1 = route_coords[i]
        lat2, lon2 = route_coords[i + 1]
        color = "green"
        for point in traffic_data_points:
            if min(lat1,lat2) <= point[0] <= max(lat1,lat2) and min(lon1,lon2) <= point[1] <= max(lon1,lon2):
                frc = traffic_data_points[point]
                if frc >= 6:
                    color = "red"
                    folium.CircleMarker(
                        location=point,
                        radius=10,
                        color="red",
                        fill=True,
                        fill_color="red",
                        fill_opacity=0.5,
                        popup=f"Traffic Congestion: {frc}"
                    ).add_to(m)
                elif frc >= 4:
                    color = "yellow"

        folium.PolyLine([route_coords[i], route_coords[i + 1]], color=color, weight=5).add_to(m)

    folium.Marker(route_coords[0], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(route_coords[-1], tooltip="End", icon=folium.Icon(color="red")).add_to(m)

    return m._repr_html_()