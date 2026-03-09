import json
from pathlib import Path
import paho.mqtt.client as mqtt
import yaml
from paho.mqtt.enums import MQTTErrorCode

def load_config(config_file="cam-config.yaml"):
    with open(config_file, "r", encoding="utf-8") as file_handle:
        config = yaml.safe_load(file_handle)
    return config or {}

class ArucoMQTTService:
    def __init__(self, id=1, detector=None, config_path="cam-config.yaml"):
        if detector is None:
            raise TypeError("Please provide a valid detector.")
        self.detector = detector


        self.config = load_config(config_path)
        mqtt_cfg = self.config.get("mqtt")
        if mqtt_cfg is None:
            raise ValueError("'mqtt' section not found in configuration file.")

        self.broker_host = mqtt_cfg.get("host", "localhost")
        self.broker_port = int(mqtt_cfg.get("port", 1883))
        self.username = mqtt_cfg.get("username")
        self.id = mqtt_cfg.get("username")
        self.password = mqtt_cfg.get("password")
        self.ca_cert_path = mqtt_cfg.get("ca_cert_path")
        if self.ca_cert_path:
            self.ca_cert_path = str((Path(config_path).parent / self.ca_cert_path).resolve())
        self.base_topic = mqtt_cfg.get("base_topic", "bip/mqtt-lab")
        configured_qos = int(mqtt_cfg.get("qos", 2))
        self.qos = 2
        if configured_qos != 2:
            print(f"Configured QoS is {configured_qos}; overriding to QoS 2.")
        self.keepalive = int(mqtt_cfg.get("keepalive", 60))

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.ca_cert_path:
            self.client.tls_set(ca_certs=self.ca_cert_path)
        if self.username:
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_host, self.broker_port, self.keepalive)
    
    # Callback when connected to MQTT broker
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with reason code {reason_code}")
        # Subscribe to the request topic
        topic = f"{self.base_topic}/{self.id}/req/#"
        (result, mid) = client.subscribe(topic, qos=self.qos)
        if result == MQTTErrorCode.MQTT_ERR_SUCCESS:
            print(f"Subscribed to topic: {topic}")
        else:
            print(f"Subscription unsuccessful to topic: {topic}")

    def on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split('/')
        res_topic = topic_parts[-2]
        command_action = topic_parts[-1]

        # Validate if the command is the correct one
        if command_action == "aruco-id":
            try:
                detected_ids, _ = self.detector.detect()

                # Prepare the response message
                # respond even if id is none.
                if detected_ids is not None:
                    marker_ids = [int(value) for row in detected_ids for value in row]
                else:
                    marker_ids = []

                # Publish the response to the response topic
                # Respond with the final position to the response topic
                response_topic = f"{self.base_topic}/{self.id}/res/{res_topic}/aruco-id"
                payload = {
                    "id": marker_ids
                }
                print(payload)
                serialized_marker_ids = json.dumps(payload)
                client.publish(response_topic, serialized_marker_ids, qos=self.qos)
                print(f"Published trajectory to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}") 
                # publish something anyway
                response_topic = f"{self.base_topic}/{self.id}/res/{res_topic}/aruco-id"
                payload = {
                    "id": []
                }
                serialized_marker_ids = json.dumps(payload)
                client.publish(response_topic, serialized_marker_ids, qos=self.qos)
                print(f"Published trajectory to topic: {response_topic}")


    # Start the MQTT client loop
    def start(self):
        # Start the MQTT loop to listen for messages
        self.client.loop_start()

    # Clean up resources
    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

