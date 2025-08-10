import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection

from src.db.database import get_connection
from src.db.queries import find_approximate_point
from src.models import Feature, FeatureCollection, Geometry
from src.services.algorithms import dijkstra_nearest_hospital

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


router = APIRouter()


async def build_feature_collection(
    path, hospital_node, distance, conn
) -> FeatureCollection:
    """
    Build a FeatureCollection from the hospital node, path, and distance.
    Args:
        path (list): List of node IDs representing the path.
        hospital_node (int): The ID of the nearest hospital node.
        distance (float): The distance to the nearest hospital.
        conn (AsyncConnection): The async connection to the database.

    Returns:
        FeatureCollection: A collection of features representing the route and hospital.
    """
    route_coordinates = []
    try:
        async with conn.cursor() as cursor:
            for i in range(len(path) - 1):
                await cursor.execute(
                    "SELECT ST_AsGeoJSON(geometry) AS geojson "
                    "FROM network_edges "
                    "WHERE from_node = %s AND to_node = %s;",
                    (path[i], path[i + 1]),
                )
                edge = await cursor.fetchone()
                if edge is None or not edge[0]:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Edge not found between node {path[i]} and {path[i+1]}",
                    )
                geom_json = json.loads(edge[0])
                route_coordinates.extend(geom_json["coordinates"])

            await cursor.execute(
                "SELECT ST_AsGeoJSON(geometry) AS geojson "
                "FROM network_hospitals "
                "WHERE node_id = %s;",
                (hospital_node,),
            )
            hospital_point = await cursor.fetchone()
            if not hospital_point:
                raise HTTPException(status_code=404, detail="Hospital node not found.")
            geom_json = json.loads(hospital_point[0])
            hospital_coordinates = geom_json["coordinates"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    route_feature = Feature(
        geometry=Geometry(
            type="LineString",
            coordinates=route_coordinates,
        ),
        properties={"distance": distance},
    )

    hospital_feature = Feature(
        geometry=Geometry(
            type="Point",
            coordinates=hospital_coordinates,
        ),
        properties={"hospital_node": hospital_node},
    )

    return FeatureCollection(features=[route_feature, hospital_feature])


@router.get("/nearest-hospital", response_model=FeatureCollection)
async def nearest_hospital(
    latitude: float, longitude: float, conn: AsyncConnection = Depends(get_connection)
) -> FeatureCollection:
    """
    Find the nearest hospital to a given latitude and longitude.
    """
    try:
        user_node_id = await find_approximate_point(latitude, longitude, conn)
    except ValueError as e:
        return {"error": str(e)}
    logger.info(f"User node ID found: {user_node_id}")

    async with conn.cursor() as cursor:
        await cursor.execute("SELECT from_node, to_node, length FROM network_edges;")
        network_edges = await cursor.fetchall()

    async with conn.cursor() as cursor:
        await cursor.execute("SELECT node_id FROM network_hospitals;")
        hospitals = set(row[0] for row in await cursor.fetchall())

    graph = {}  # Create an adjacency list for the graph
    for u, v, length in network_edges:
        graph.setdefault(u, []).append((v, length))

    hospital_node, path, distance = dijkstra_nearest_hospital(
        graph, user_node_id, hospitals
    )
    if path is None:
        raise HTTPException(status_code=404, detail="No path to any hospital found.")

    if len(path) == 1:
        logger.info("User is already at a hospital.")
        return FeatureCollection(
            features=[
                Feature(
                    geometry=Geometry(
                        type="Point",
                        coordinates=[longitude, latitude],
                    ),
                    properties={"message": "You are already at a hospital."},
                )
            ]
        )

    logger.info(f"Nearest hospital node: {hospital_node}, Distance: {distance}")
    feature_collection = await build_feature_collection(
        path, hospital_node, distance, conn
    )
    return feature_collection
