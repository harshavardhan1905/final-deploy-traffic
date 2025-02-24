from fastapi import FastAPI, HTTPException
import requests
import folium
import openrouteservice
from fastapi.responses import HTMLResponse
import math

app = FastAPI()

# Replace with your own keys
TOMTOM_API_KEY = "eZEcIlVKK9lGUqDzqLtnm8b7xOG1FfFG"
ORS_API_KEY = "5b3ce3597851110001cf624882ff503deb274a2981515b5272c8cb05"
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
TOMTOM_TRAFFIC_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance (in km) between two points
    on the Earth (lat1, lon1) and (lat2, lon2).
    """
    R = 6371.0  # Earth radius in km
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def fetch_route(origin: str, destination: str):
    """Fetch route data from ORS API."""
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    try:
        origin_lon, origin_lat = map(float, origin.split(","))
        destination_lon, destination_lat = map(float, destination.split(","))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid coordinate format. Use 'longitude,latitude'."
        )

    location_data = {
        "coordinates": [[origin_lon, origin_lat], [destination_lon, destination_lat]],
        "geometry": True
    }

    response = requests.post(ORS_URL, json=location_data, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"ORS API Error: {response.text}"
        )

    data = response.json()
    if "routes" not in data or not data["routes"]:
        raise HTTPException(
            status_code=404,
            detail="No route found. Check if the locations are reachable."
        )

    return data

def get_traffic(lat: float, lon: float):
    """Fetch real-time traffic flow data from TomTom."""
    params = {"key": TOMTOM_API_KEY, "point": f"{lat},{lon}"}
    response = requests.get(TOMTOM_TRAFFIC_URL, params=params)
    if response.status_code != 200:
        return None
    return response.json()

@app.get("/map", response_class=HTMLResponse)
def show_map(origin: str, destination: str):
    """
    Generate a Folium map showing the route from origin to destination.
    Fetches real-time traffic data from TomTom and:
    - Colors route segments green/yellow/red
    - Calculates total delay (in minutes) for yellow/red segments
    - Shows the estimated time to reach the destination
    """
    # 1) Fetch the route from ORS
    data = fetch_route(origin, destination)
    
    # Extract the *ORS-calculated* travel time (in seconds) for this route
    # NOTE: ORS's "duration" may already include typical traffic, but not necessarily real-time
    route_summary_time_s = data["routes"][0]["summary"]["duration"]
    route_summary_time_min = route_summary_time_s / 60.0  # Convert seconds -> minutes

    # Decode the route polyline
    route_coords = openrouteservice.convert.decode_polyline(
        data["routes"][0]["geometry"]
    )
    route_coords = [(coord[1], coord[0]) for coord in route_coords["coordinates"]]

    # 2) Create Folium map centered on the start
    m = folium.Map(location=route_coords[0], zoom_start=13)

    # Keep track of whether we found red segments
    heavy_traffic_found = False

    # We'll also accumulate total traffic delay in minutes
    total_delay_minutes = 0.0

    # 3) Segment the route & color by traffic flow
    segment_length = max(1, len(route_coords) // 30)
    for i in range(0, len(route_coords) - 1, segment_length):
        mid_index = i + segment_length // 2
        if mid_index >= len(route_coords):
            mid_index = len(route_coords) - 1

        # We'll calculate the approximate distance of this segment
        segment_distance_km = 0.0
        segment_points = route_coords[i : i + segment_length + 1]

        # Sum up distances between each consecutive point in the segment
        for j in range(len(segment_points) - 1):
            lat1, lon1 = segment_points[j]
            lat2, lon2 = segment_points[j + 1]
            segment_distance_km += haversine(lat1, lon1, lat2, lon2)

        # Check traffic at the midpoint
        mid_lat, mid_lon = route_coords[mid_index]
        traffic_data = get_traffic(mid_lat, mid_lon)

        color = "blue"  # default
        if traffic_data and "flowSegmentData" in traffic_data:
            speed = traffic_data["flowSegmentData"].get("currentSpeed", 0)  # km/h
            free_flow_speed = traffic_data["flowSegmentData"].get("freeFlowSpeed", 1)  # km/h
            if free_flow_speed == 0:
                free_flow_speed = 1  # avoid division by zero

            # Congestion level = currentSpeed / freeFlowSpeed
            congestion_level = speed / free_flow_speed

            # Time in hours for this segment at free flow vs current speed
            time_free_flow_hr = segment_distance_km / free_flow_speed
            time_current_hr = segment_distance_km / speed if speed else float('inf')

            # Convert to minutes
            time_free_flow_min = time_free_flow_hr * 60
            time_current_min = time_current_hr * 60

            # Additional delay for this segment
            delay_segment = max(0, time_current_min - time_free_flow_min)
            total_delay_minutes += delay_segment

            # Color the segment
            if congestion_level > 0.7:
                color = "green"       # mostly free-flow
            elif congestion_level > 0.4:
                color = "yellow"      # moderate traffic
            else:
                color = "red"         # heavy traffic
                heavy_traffic_found = True

        # Draw the segment on the map
        folium.PolyLine(
            segment_points,
            color=color,
            weight=5,
            opacity=0.7
        ).add_to(m)

    # 4) Mark start and end
    folium.Marker(
        route_coords[0],
        tooltip="Start",
        icon=folium.Icon(color="green")
    ).add_to(m)

    folium.Marker(
        route_coords[-1],
        tooltip="End",
        icon=folium.Icon(color="red")
    ).add_to(m)

    # 5) Calculate final estimated time (in minutes)
    # ORS duration + real-time delay from TomTom
    total_estimated_time_min = route_summary_time_min + total_delay_minutes

    # Round values to 2 decimal places
    base_time_str = f"{round(route_summary_time_min, 2)}"
    delay_str = f"{round(total_delay_minutes, 2)}"
    final_time_str = f"{round(total_estimated_time_min, 2)}"

    # 6) Show a marker with traffic/time info
    midpoint = route_coords[len(route_coords) // 2]
    if heavy_traffic_found:
        tooltip_text = (
            f"Heavy Traffic Detected!\n"
            f"Base Time (ORS): ~{base_time_str} min\n"
            f"Traffic Delay: ~{delay_str} min\n"
            f"Total Est. Time: ~{final_time_str} min"
        )
        folium.Marker(
            midpoint,
            tooltip=tooltip_text,
            icon=folium.Icon(color="orange", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)
    else:
        tooltip_text = (
            f"No Major Traffic!\n"
            f"Base Time (ORS): ~{base_time_str} min\n"
            f"Traffic Delay: ~{delay_str} min\n"
            f"Total Est. Time: ~{final_time_str} min"
        )
        folium.Marker(
            midpoint,
            tooltip=tooltip_text,
            icon=folium.Icon(color="blue", icon="info-sign", prefix="fa")
        ).add_to(m)

    return m._repr_html_()
