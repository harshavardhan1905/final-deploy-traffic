# Real-Time Route Suggestion with FastAPI & Folium

This project provides a **real-time traffic route suggestion** system using **FastAPI** (Python), **TomTom** traffic data, and **Folium** for map visualization. It dynamically fetches traffic information and calculates:

- **Color-coded** route segments (green, yellow, red) based on congestion.
- **Estimated travel time** at the end marker, factoring in **traffic delays**.

---

## Table of Contents
1. [Features](#features)  
2. [Tech Stack & Requirements](#tech-stack--requirements)  
3. [Installation & Setup](#installation--setup)  
4. [Usage](#usage)  
5. [Embedding the Map in HTML](#embedding-the-map-in-html)  
6. [Future Improvements](#future-improvements)  
7. [License](#license)

---

## Features

- **FastAPI** backend that handles route requests.
- **OpenRouteService (ORS)** to compute base route and travel time.
- **TomTom Traffic API** to fetch real-time congestion levels.
- **Folium** to render interactive maps in HTML.
- **Color-coded** segments:
  - **Green**: Low congestion  
  - **Yellow**: Moderate congestion  
  - **Red**: Heavy congestion  
- **End Marker** shows:
  - **Base Time** from ORS  
  - **Traffic Delay** from TomTom  
  - **Final Estimated Time**

---

## Tech Stack & Requirements

- **Python 3.8+**
- **FastAPI** for the web server
- **Uvicorn** for running FastAPI
- **Requests** to call external APIs (TomTom, ORS)
- **Folium** for map rendering
- **OpenRouteService** Python client for decoding polylines

**APIs Needed**  
1. **OpenRouteService**: [https://openrouteservice.org/](https://openrouteservice.org/)  
2. **TomTom Traffic**: [https://developer.tomtom.com/](https://developer.tomtom.com/)

You will need **API keys** for both services.

---

## Installation & Setup

1. **Clone** the repository (or download the source code):

   ```bash
   git clone https://github.com/YourUsername/RealTimeRouteSuggestion.git
   cd RealTimeRouteSuggestion
##Create a virtual environment (optional but recommended):
