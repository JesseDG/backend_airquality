import firebase_admin
from firebase_admin import credentials
import json

from dotenv import load_dotenv
load_dotenv()

# Initialize Firebase Admin SDK
#cred = credentials.Certificate("./qualiair_fcm_key.json") #for dev only
cred = credentials.Certificate("./etc/secrets/qualiair_fcm_key.json")
firebase_admin.initialize_app(cred)

from fastapi import FastAPI
from influxdb import init_client, start_subscriber
from history import get_history
from contextlib import asynccontextmanager
from models import RegisterDeviceRequest, UpdateThresholdsRequest, DeviceDocument
from firestore import db
from notification import invalidate_cache, preload_cache, add_device_to_cache




@asynccontextmanager
async def lifespan(app: FastAPI):
    init_client()
    start_subscriber()
    preload_cache() # Preload device data into cache on startup
    yield
    # Cleanup on shutdown
    from influxdb import client
    if client:
        client.close()
        print("✅ InfluxDB client closed")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "running"}

#endpoint for history here
@app.get("/history")
async def history(range: str, sensor: str, device_id: str):
    # Placeholder for fetching historical data from InfluxDB
    return await get_history(range, sensor, device_id)

#end point for FCM token received from android
@app.post("/register")
async def register_token(req: RegisterDeviceRequest):
    print("Received device registration request:", json.dumps(req.model_dump(), indent=2))
    try:
        # Validate the request data using Pydantic
        req = RegisterDeviceRequest(**req.model_dump())   
        db.collection("devices").document(req.device_id).set({
            "token":  req.token,
            "thresholds": req.thresholds.model_dump()
        }) 
        # Add to cache immediately after registration
        add_device_to_cache(req.device_id, DeviceDocument(token=req.token, thresholds=req.thresholds))
        return {"status": "token registered"}
    except Exception as e:
        print(f"Error validating request: {e}")
        return {"status": "invalid request - not registered"}

#end point for updating the thresholds
@app.post("/update")
async def update_thresholds(req: UpdateThresholdsRequest):
    # Placeholder for updating the thresholds in a database or in-memory store
    print("Updating thresholds:", json.dumps(req.model_dump(), indent=2))
    try:
        db.collection("devices").document(req.device_id).update({
            "thresholds": req.thresholds.model_dump()
        })
        invalidate_cache(req.device_id) # Invalidate cache for this device to ensure updated thresholds are used
        return {"status": "thresholds updated"}
    except Exception as e:
        print(f"Error updating thresholds: {e}")
        return {"status": "invalid request - thresholds not updated"}
    
@app.get("/cache")
def get_cache():
    from notification.monitoring import _cache
    return {device_id: device.model_dump() for device_id, device in _cache.items()}