from fastapi import FastAPI, HTTPException, WebSocket
import uuid
from fastapi.staticfiles import StaticFiles 
import asyncio
from position_tracker import PositionTracker
import requests
import folium
import openrouteservice
from fastapi.responses import HTMLResponse,FileResponse
from route_service import (
    fetch_route,
    get_traffic,
    get_incidents,
    calculate_eta,
    TOMTOM_API_KEY,
    ORS_API_KEY
)

app = FastAPI()
# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")
position_tracker = PositionTracker()

@app.get("/")
async def read_root():
    return FileResponse("./templates/index.html")

@app.websocket("/ws/position/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await position_tracker.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            await position_tracker.update_position(
                client_id,
                data["latitude"],
                data["longitude"]
            )
            # Update the map with new position
            await websocket.send_json({
                "type": "position_update",
                "latitude": data["latitude"],
                "longitude": data["longitude"]
            })
            await asyncio.sleep(10)  # Update every 10 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        position_tracker.disconnect(client_id)



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
    # Collect traffic data for route segments
    traffic_data_list = []
    segment_length = max(1, len(route_coords) // 30)
    for i in range(0, len(route_coords) - 1, segment_length):
        mid_index = i + segment_length // 2
        if mid_index >= len(route_coords):
            mid_index = len(route_coords) - 1
        mid_lat, mid_lon = route_coords[mid_index]
        traffic_data = get_traffic(mid_lat, mid_lon)
        traffic_data_list.append(traffic_data)
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
    # Calculate ETA after collecting traffic data
    eta_info = calculate_eta(route_coords, traffic_data_list)
    
    # Add ETA information box to map
    eta_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; z-index: 1000; 
                background-color: white; padding: 10px; border: 2px solid grey; 
                border-radius: 5px; font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0;">Journey Information</h4>
        <p style="margin: 5px 0;"><strong>ETA:</strong> {eta_info['arrival_time']}</p>
        <p style="margin: 5px 0;"><strong>Duration:</strong> {eta_info['total_time_minutes']} mins</p>
        <p style="margin: 5px 0;"><strong>Distance:</strong> {eta_info['total_distance_km']} km</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(eta_html))

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

