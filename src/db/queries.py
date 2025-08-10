from psycopg import AsyncConnection

from src.db.database import get_connection


async def find_approximate_point(
    latitude: float, longitude: float, conn: AsyncConnection
) -> int:
    """
    Find the nearest node in the network to a given latitude and longitude.

    Args:
        latitude (float): Latitude of the point.
        longitude (float): Longitude of the point.
        conn (AsyncConnection): The async connection to the database.

    Returns:
        int: The ID of the nearest node.
    """
    query = """
    SELECT node_id 
    FROM network_nodes
    ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
    LIMIT 1;
    """

    async with conn.cursor() as cursor:
        await cursor.execute(query, (longitude, latitude))
        result = await cursor.fetchone()
        if result:
            return result[0]
        else:
            raise ValueError("No nodes found in the network.")


async def assign_hospital_to_node():
    """
    Assign a hospital to the nearest node in the network.
    """
    query = """
    ALTER TABLE network_hospitals
    ADD COLUMN IF NOT EXISTS node_id BIGINT;

    UPDATE network_hospitals h
    SET node_id = (
        SELECT node_id
        FROM network_nodes n
        ORDER BY h.geometry <-> n.geometry
        LIMIT 1
    );
    """
    try:
        async for conn in get_connection():
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                await conn.commit()
    except Exception as e:
        print(f"Error assigning hospital nodes: {e}")
        await conn.rollback()
