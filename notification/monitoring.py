from notification.fcm import send_notification
from models import DeviceDocument
from firestore import db
from datetime import datetime, timedelta

# Cache stores the full DeviceDocument model, not raw dicts
_cache: dict = {}
COOLDOWN = timedelta(seconds=30)
_last_notified: dict = {} # (device_id, alarm_key) -> datetime of last notification sent

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
    alarms = []

    if h2s >= t.alert_h2s:
        alarms.append(("h2s_alert", f"🔴 H2S critical: {h2s} ppm"))
    elif h2s >= t.caution_h2s:
        alarms.append(("h2s_caution", f"🟡 H2S warning: {h2s} ppm"))

    if nh3 >= t.alert_nh3:
        alarms.append(("nh3_alert", f"🔴 NH3 critical: {nh3} ppm"))
    elif nh3 >= t.caution_nh3:
        alarms.append(("nh3_caution", f"🟡 NH3 warning: {nh3} ppm"))

    if dust >= t.alert_dust:
        alarms.append(("dust_alert", f"🔴 Dust critical: {dust} µg/m³"))
    elif dust >= t.caution_dust:
        alarms.append(("dust_caution", f"🟡 Dust warning: {dust} µg/m³"))

    if not alarms:
        # Clear all cooldowns for this device when conditions return to normal
        for key in list(_last_notified):
            if key[0] == device_id:
                del _last_notified[key]
        return

    now = datetime.now()
    for alarm_key, message in alarms:
        cd_key = (device_id, alarm_key)
        last = _last_notified.get(cd_key)
        if last and (now - last) < COOLDOWN:
            continue # This specific alarm is still in cooldown
        _last_notified[cd_key] = now
        send_notification(device.token, "⚠️ Air Quality Alert", message)

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