from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from influxdb import init_client, start_subscriber
from history import get_history
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_client()
    start_subscriber()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "running"}

#endpoint for history here
@app.get("/history")
async def history(range: str, sensor: str, device_id: str):
    # Placeholder for fetching historical data from InfluxDB
    return await get_history(range, sensor, device_id)