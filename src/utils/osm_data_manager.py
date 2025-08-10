import logging

import osmnx as ox
import psycopg

from src.config.settings import settings

ox.settings.use_cache = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class OSMDataManager:
    """
    A class to manage the OpenStreetMap data loading
    for fetching and transforming road network data and hospital locations
    in a specified city and storing them in a PostgreSQL database.
    """

    def __init__(self):
        """Initialize the OSMDataManager with settings."""
        self.database_url = settings.database_url
        self.city = "Paris, France"
        self.network_type = "drive"

    def fetch_network_data(self):
        """Fetch the road network data for the specified city."""
        logger.info(
            f"Fetching road network data for {self.city} with network type '{self.network_type}'"
        )
        G = ox.graph_from_place(self.city, network_type=self.network_type)
        nodes, edges = ox.graph_to_gdfs(G)
        nodes = nodes.reset_index()
        edges = edges.reset_index()
        logger.info(f"Fetched {len(nodes)} nodes and {len(edges)} edges")
        return nodes, edges

    def fetch_hospitals(self):
        """Fetch hospitals in the specified city."""
        logger.info(f"Fetching hospitals in {self.city}")
        hospitals = ox.features_from_place(self.city, tags={"amenity": "hospital"})
        hospitals = hospitals.reset_index()
        logger.info(f"Fetched {len(hospitals)} hospitals")
        return hospitals

    def transform_nodes(self, nodes):
        """Transform nodes to include latitude and longitude."""
        logger.info("Transforming nodes")
        nodes = nodes.rename(
            columns={"y": "latitude", "x": "longitude", "osmid": "node_id"}
        )
        nodes = nodes[["node_id", "latitude", "longitude", "geometry", "street_count"]]
        nodes["geometry"] = nodes["geometry"].apply(lambda geom: geom.wkt)
        logger.info(f"Transformed nodes: {nodes.head(2)}")
        return nodes

    def transform_edges(self, edges):
        """Transform edges to include necessary attributes."""
        logger.info("Transforming edges")
        edges = edges.rename(columns={"u": "from_node", "v": "to_node"})
        edges = edges[["from_node", "to_node", "geometry", "length"]]
        edges = edges.drop_duplicates(subset=["from_node", "to_node"], keep="first")
        edges["geometry"] = edges["geometry"].apply(lambda geom: geom.wkt)
        logger.info(f"Transformed edges: {edges.head(2)}")
        return edges

    def transform_hospitals(self, hospitals):
        """Transform hospitals to ensure they are in the correct format."""
        logger.info("Transforming hospitals")
        hospitals["geometry"] = hospitals["geometry"].apply(
            lambda geom: geom if geom.geometryType == "Point" else geom.centroid
        )
        hospitals = hospitals.rename(columns={"id": "hospital_id"})
        hospitals = hospitals[["hospital_id", "geometry"]]
        hospitals["geometry"] = hospitals["geometry"].apply(lambda geom: geom.wkt)
        logger.info(f"Transformed hospitals: {hospitals.head(2)}")
        return hospitals

    def validate_nodes(self, nodes):
        """Validate nodes to ensure no missing coordinates."""
        required_columns = [
            "node_id",
            "latitude",
            "longitude",
            "geometry",
            "street_count",
        ]
        missing_columns = [col for col in required_columns if col not in nodes.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in nodes: {', '.join(missing_columns)}"
            )

        if (
            not nodes["latitude"].notnull().all()
            or not nodes["longitude"].notnull().all()
        ):
            raise ValueError("Nodes contain missing latitude or longitude values.")

        logger.info("Node validation passed")
        return True

    def validate_edges(self, edges, nodes):
        """Validate edges to ensure they reference valid nodes."""
        required_columns = ["from_node", "to_node", "geometry", "length"]
        missing_columns = [col for col in required_columns if col not in edges.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in edges: {', '.join(missing_columns)}"
            )
        if (
            not edges["from_node"].isin(nodes["node_id"]).all()
            or not edges["to_node"].isin(nodes["node_id"]).all()
        ):
            raise ValueError("Edges reference invalid nodes.")

        if (edges["length"] <= 0).any():
            raise ValueError("Negative or zero edge lengths found!")
        logger.info("Edge validation passed")
        return True

    def validate_hospitals(self, hospitals):
        """Validate hospitals to ensure they have valid geometries."""
        required_columns = ["hospital_id", "geometry"]
        missing_columns = [
            col for col in required_columns if col not in hospitals.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in hospitals: {', '.join(missing_columns)}"
            )

        logger.info("Hospital validation passed")
        return True

    def load_into_database(self, nodes, edges, hospitals):
        """Load the transformed data into the PostgreSQL database."""
        logger.info("Loading data into the database")
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cursor:
                for _, row in nodes.iterrows():
                    cursor.execute(
                        """
     
                    INSERT INTO network_nodes (node_id, latitude, longitude, geometry, street_count)
                    VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), %s)
                    ON CONFLICT (node_id) DO NOTHING;
                    """,
                        (
                            row["node_id"],
                            row["latitude"],
                            row["longitude"],
                            row["geometry"],
                            row["street_count"],
                        ),
                    )

                for _, row in edges.iterrows():
                    cursor.execute(
                        """
                    INSERT INTO network_edges (from_node, to_node, geometry, length)
                    VALUES (%s, %s, ST_GeomFromText(%s, 4326), %s)
                    ON CONFLICT (from_node, to_node) DO NOTHING;
                    """,
                        (
                            row["from_node"],
                            row["to_node"],
                            row["geometry"],
                            row["length"],
                        ),
                    )

                for _, row in hospitals.iterrows():
                    cursor.execute(
                        """
                    INSERT INTO network_hospitals (hospital_id, geometry)
                    VALUES (%s, ST_GeomFromText(%s, 4326))
                    ON CONFLICT (hospital_id) DO NOTHING;
                    """,
                        (row["hospital_id"], row["geometry"]),
                    )

                conn.commit()
        logger.info("Data loaded into the database successfully")
