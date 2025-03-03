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

## 1.Features

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

## 2.Tech Stack & Requirements

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

## 3.Installation & Setup

1. **Clone** the repository (or download the source code):

   ```bash
       git clone https://github.com/harshavardhan1905/final-deploy-traffic.git
       cd RealTimeRouteSuggestion
2. **Create a virtual environment (optional but recommended):**
   ```bash
      python -m venv venv
      source venv/bin/activate  # Linux/Mac
      venv\Scripts\activate     # Windows
## Snapshots:
    ![image](https://github.com/user-attachments/assets/56a4b6c2-be3c-4620-a6b3-f857d79deead)
**Initial**
![Screenshot 2025-02-28 152748](https://github.com/user-attachments/assets/76666af1-d4f6-40d7-ae8b-d1e32e631f28)
**Source & Destination**
![image](https://github.com/user-attachments/assets/2dd19679-464c-4955-a5e4-2dbea4b3b025)
**Live Traffic**
![image](https://github.com/user-attachments/assets/f9e713a6-2b09-4874-a134-941626ae3ce0)
**Response proof:**
![image](https://github.com/user-attachments/assets/c699b24a-0d91-4e6f-9b0e-4cf45a00d3a9)




## 4.Usage
1.  **Run the FastAPI server:**
    ```bash
      uvicorn main:app --reload
3.  **Access the map in your browser at:**
   ```bash
       http://127.0.0.1:8000/map?origin=LONG,LAT&destination=LONG,LAT

   
