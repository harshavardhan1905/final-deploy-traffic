# Real-Time Route Suggestion

This project displays real-time traffic data on a Folium map, with the **final travel time** shown at the end point.

## Example HTML Embedding


<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Real-Time Route Suggestion</title>
</head>
<body>
  <h1>Real-Time Route Suggestion</h1>
  <p>
    The map below is served by our FastAPI endpoint at
    <code>http://localhost:8000/map?origin=LONG,LAT&amp;destination=LONG,LAT</code>.
  </p>
  
  <!-- Adjust width, height, and styling as needed -->
  <iframe 
      src="http://localhost:8000/map?origin=78.53645,17.44957&destination=78.48838,17.60214"
      width="100%"
      height="600"
      style="border:none;">
  </iframe>
</body>
</html>

---

### **How It Works**

- The **`<iframe>`** points to your **FastAPI** route, which returns an **HTML page** containing the Folium map.  
- **GitHub** won’t render this **iframe** in the README, but it provides an example of how others could embed your map in their own HTML pages.  

That’s it! Feel free to customize the **styling**, **dimensions**, or **text** to match your project’s needs.


