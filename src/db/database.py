from psycopg import AsyncConnection

from src.config.settings import settings


async def get_connection():
    """Get an async connection to the PostgreSQL database using psycopg3."""
    conn = await AsyncConnection.connect(settings.database_url)
    try:
        yield conn
    finally:
        await conn.close()
