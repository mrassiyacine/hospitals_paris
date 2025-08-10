from src.utils.osm_data_manager import OSMDataManager


def populate_database():
    """Run the OSM data loading process."""
    manager = OSMDataManager()
    # Fetch the data
    nodes, edges = manager.fetch_network_data()
    hospitals = manager.fetch_hospitals()
    # Transform the data
    nodes = manager.transform_nodes(nodes)
    edges = manager.transform_edges(edges)
    hospitals = manager.transform_hospitals(hospitals)
    # Validate the data
    manager.validate_nodes(nodes)
    manager.validate_edges(edges, nodes)
    manager.validate_hospitals(hospitals)
    # Load the data into the database
    manager.load_into_database(nodes, edges, hospitals)
