# Nearest Hospital Finder

This project enables users to click anywhere on a map (within Paris) and find the shortest driving path to the nearest hospital, calculated approximately from the selected point.

This project consists of three main services:

### 1. Database Service
- **Image:** [PostGIS](https://hub.docker.com/r/postgis/postgis/)
- **Schema:** See `data/init.sql`
  - **network_nodes:** Road network nodes (intersections/points), with latitude, longitude, geometry, and optional street count.
  - **network_edges:** Directed edges between nodes representing road segments, with geometry and length.
  - **network_hospitals:** Hospital locations as nodes, with geometry.

### 2. Backend Service (FastAPI)
- **Pre-launch step:** Use the `OsmDataManager` (`app/db/osmDataManager`) to fetch, validate, transform, and load OSM data into PostGIS.
- **Router:** `/nearest-hospital`
  - **Input:** Latitude and longitude within Paris boundaries.
  - **Output:** GeoJSON containing the path to the nearest hospital.
- **Algorithms:** Pure Python Dijkstra implementation in `services/algorithms` (for fun, without relying on PostGIS functions or libraries like NetworkX).

### 3. Frontend Service
- **User Interaction:** Click anywhere within Paris boundaries to query the backend and visualize the shortest path to the nearest hospital.

## How to Use

1. **Start all services with Docker Compose:**
   ```sh
   git clone git@github.com:mrassiyacine/hospitals_paris.git
   cd hospitals_paris
   docker-compose up
   ```

2. **Access the application:**

   - Open your browser and go to [http://localhost:3000](http://localhost:3000).

3. **Usage:**
   - Click anywhere within Paris boundaries on the map to find and display the shortest driving path to the nearest hospital.

Make sure PostGIS and backend services are initialized and populated before using the frontend.

## Screenshots

Below are some example screenshots of the app in action:

![containers running](images/container.png)
*Service/containers running.*


![Hospital Query Example](images/example1.png)
*Shortest path to nearest hospital displayed on the map.*


![Out of the city](images/example2.png)
* Clicked location outside Paris boundaries*