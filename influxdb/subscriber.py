import paho.mqtt.client as mqtt
from influxdb_client import Point
from . import client as client_module
from influxdb_client.client.write_api import SYNCHRONOUS
import os
import json

HIVEMQ_HOST = os.getenv("HIVEMQ_HOST")
HIVEMQ_PORT = int(os.getenv("HIVEMQ_PORT"))
HIVEMQ_TOPIC = os.getenv("HIVEMQ_TOPIC")
HIVEMQ_USER = os.getenv("HIVEMQ_USER")
HIVEMQ_PASSWORD = os.getenv("HIVEMQ_PASSWORD")

#
#   MQTT connector callback - handles connection to HiveMQ 
#
#   mqttc: MQTT client instance
#   userdata: User data passed to callbacks
#   flags: Response flags sent by the broker
#   rc: Connection result code from HiveMQ
# 
def on_connect(mqttc, userdata, flags, rc):
    if rc == 0:
        if(mqttc.subscribe(HIVEMQ_TOPIC)):
            print("Connected to MQTT Broker successfully.......")
            print(f"Subscribed to topic {HIVEMQ_TOPIC} successfully.......")
        else:
            print(f"Failed to subscribe to topic {HIVEMQ_TOPIC}.......")
    else:
        print(f"Failed to connect to HiveMQ, return code {rc}")

#  MQTT message callback - processes incoming messages and writes to InfluxDB
#   mqttc: MQTT client instance
#   userdata: User data passed to callbacks
#   msg: MQTT message object containing topic and payload

def on_message(mqttc, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received message on topic {msg.topic}: {payload}")
        # Create InfluxDB Point with tags and fields based on the incoming payload
        # Assuming payload contains device_id, ammonia, hydrogen_sulfide, humidity, voc, dust, timestamp
        # air_quality_data would be considered the table in influxdb
        point = Point("air_quality_data") \
            .tag("device_id", payload.get("device_id", "unknown")) \
            .field("ammonia", payload.get("ammonia")) \
            .field("hydrogen_sulfide", payload.get("hydrogen_sulfide")) \
            .field("humidity", payload.get("humidity")) \
            .field("temperature", payload.get("temperature")) \
            .field("dust", payload.get("dust")) \
            .field("pressure", payload.get("pressure")) \
            .field("timestamp", payload.get("timestamp"))
        
        write_client = client_module.client.write_api(write_options=SYNCHRONOUS)
        write_client.write(bucket=client_module.INFLUXDB_BUCKET, org=client_module.INFLUXDB_ORG, record=point)
        print("Data written to InfluxDB successfully.......")
    except Exception as e:
        print(f"Error processing message: {e}")

def start_subscriber():
    mqttc = mqtt.Client()
    # mqttc.tls_set()  # only for production HiveMQ
    mqttc.username_pw_set(HIVEMQ_USER, HIVEMQ_PASSWORD)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message

    try:
        mqttc.connect(HIVEMQ_HOST, HIVEMQ_PORT, 60)
        mqttc.loop_start()
    except Exception as e:
        print(f"Error connecting to HiveMQ: {e}")