from pydantic import BaseModel

class Thresholds(BaseModel):
    caution_h2s:    float = 1.0
    alert_h2s:      float = 5.0
    caution_nh3:    float = 25.0
    alert_nh3:      float = 35.0
    caution_dust:   float = 12.0
    alert_dust:     float = 35.0

class DeviceDocument(BaseModel):
    token:  str
    thresholds: Thresholds = Thresholds()

class RegisterDeviceRequest(BaseModel):
    device_id:  str
    token:  str
    thresholds: Thresholds = Thresholds()

class UpdateThresholdsRequest(BaseModel):
    device_id:  str
    thresholds: Thresholds