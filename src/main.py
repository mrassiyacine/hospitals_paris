import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.populate_database import populate_database
from src.db.queries import assign_hospital_to_node
from src.routers.nearest_hospital import router as network_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """lifespan event handler for the FastAPI application."""
    logger.info("Starting up the application...")
    try:
        populate_database()
        logger.info("Database populated successfully.")
        await assign_hospital_to_node()
        logger.info("Assigned hospitals to nodes successfully.")
        yield

    finally:
        logger.info("Shutting down the application...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to the Hospitals Paris API!"}


app.include_router(network_router, prefix="/api", tags=["network"])
