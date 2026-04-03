from notification.fcm import send_notification
from models import DeviceDocument
from firestore import db
from datetime import datetime, timedelta

# Cache stores the full DeviceDocument model, not raw dicts
_cache: dict = {}
COOLDOWN = timedelta(seconds=30)
_last_notified: dict = {} # device_id -> datetime of last notification sent

def preload_cache():
    docs = db.collection("devices").stream()
    for doc in docs:
        _cache[doc.id] = DeviceDocument(**doc.to_dict())
    print(f"Cache preloaded with {len(_cache)} devices")

def monitor_thresholds(device_id: str, nh3: float, h2s: float, dust: float):
    # Placeholder for monitoring logic to compare incoming sensor data against thresholds
    # This function would be called whenever new sensor data is received for a device
    print(f"Monitoring thresholds for device {device_id} with NH3: {nh3}, H2S: {h2s}, Dust: {dust}")
    device = get_device_cached(device_id)
    if not device:
        print(f"Device {device_id} not registered yet, skipping")
        return

    t = device.thresholds
    messages = []

    if h2s >= t.alert_h2s:
        messages.append(f"🔴 H2S critical: {h2s} ppm")
    elif h2s >= t.caution_h2s:
        messages.append(f"🟡 H2S warning: {h2s} ppm")

    if nh3 >= t.alert_nh3:
        messages.append(f"🔴 NH3 critical: {nh3} ppm")
    elif nh3 >= t.caution_nh3:
        messages.append(f"🟡 NH3 warning: {nh3} ppm")

    if dust >= t.alert_dust:
        messages.append(f"🔴 Dust critical: {dust} µg/m³")
    elif dust >= t.caution_dust:
        messages.append(f"🟡 Dust warning: {dust} µg/m³")

    if not messages:# Clear cooldown if conditions are back to normal
        _last_notified.pop(device_id, None)
        return

    now = datetime.now()
    last = _last_notified.get(device_id)
    if last and (now - last) < COOLDOWN:
        return # Skip sending notification if we're still in cooldown period
    
    _last_notified[device_id] = now # Update the last notified time
    send_notification(device.fcm_token, "⚠️ Air Quality Alert", ", ".join(messages))

#   Helper function to get device information from cache or Firestore
def get_device_cached(device_id: str):
    if device_id in _cache:
        return _cache[device_id] # Return the cached DeviceDocument

    doc = db.collection("devices").document(device_id).get()
    if not doc.exists:
        return None

    device = DeviceDocument(**doc.to_dict())
    _cache[device_id] = device
    return device

def invalidate_cache(device_id: str):
    _cache.pop(device_id, None)

def add_device_to_cache(device_id: str, device_doc: DeviceDocument):
    _cache[device_id] = device_doc