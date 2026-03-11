from pathlib import Path
import json
import re
import threading
import time

import paho.mqtt.client as mqtt
import serial
import yaml


def load_config(config_file="config.yaml"):
    with open(config_file, "r", encoding="utf-8") as file_handle:
        config = yaml.safe_load(file_handle)
    return config or {}


class ConveyorMQTTService:
    def __init__(self, config_path="config.yaml"):
        self.config = load_config(config_path)

        mqtt_cfg = self.config.get("mqtt")
        if mqtt_cfg is None:
            raise ValueError("'mqtt' section not found in configuration file.")

        self.broker_host = mqtt_cfg.get("host", "localhost")
        self.broker_port = int(mqtt_cfg.get("port", 1883))
        self.base_topic = mqtt_cfg.get("base_topic", "bip/mqtt-lab")
        self.qos = int(mqtt_cfg.get("qos", 2))
        self.keepalive = int(mqtt_cfg.get("keepalive", 60))

        self.username = mqtt_cfg.get("username")
        self.id = mqtt_cfg.get("username")
        self.password = mqtt_cfg.get("password")
        self.ca_cert_path = mqtt_cfg.get("ca_cert_path")
        if self.ca_cert_path:
            self.ca_cert_path = str((Path(config_path).parent / self.ca_cert_path).resolve())

        serial_cfg = self.config.get("serial", {})
        self.serial_port = serial_cfg.get("port", "COM5")
        self.baud_rate = int(serial_cfg.get("baud_rate", 115200))
        self.serial_timeout = float(serial_cfg.get("timeout", 1.0))

        self.request_id = ""
        self.serial_thread = None
        telemetry_cfg = self.config.get("telemetry", {})
        self.telemetry_enabled = bool(telemetry_cfg.get("enabled", True))
        self.telemetry_rate_hz = float(telemetry_cfg.get("publish_rate_hz", 0))
        self._telemetry_last_publish_ts = 0.0

        self._update_topics()
        self.ser = self._create_serial_connection()

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.ca_cert_path:
            self.client.tls_set(ca_certs=self.ca_cert_path)
        if self.username:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_host, self.broker_port, self.keepalive)

    def _create_serial_connection(self):
        try:
            return serial.Serial(self.serial_port, self.baud_rate, timeout=self.serial_timeout)
        except serial.SerialException as exc:
            print(f"Failed to initialize serial connection: {exc}")
            return None

    def _update_topics(self):
        self.sub_topic = f"{self.base_topic}/{self.id}/req/#"
        self.respond_topic = f"{self.base_topic}/{self.id}/res/"
        self.pub_topic = f"{self.base_topic}/{self.id}/telemetry"

    def _should_publish_telemetry(self):
        if not self.telemetry_enabled:
            return False

        if self.telemetry_rate_hz <= 0:
            return True

        now = time.monotonic()
        min_interval = 1.0 / self.telemetry_rate_hz
        if (now - self._telemetry_last_publish_ts) < min_interval:
            return False

        self._telemetry_last_publish_ts = now
        return True

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.sub_topic, qos=self.qos)
            print("subscribed to :" + self.sub_topic)
        else:
            print(f"Failed to connect, return code {reason_code}")

    def on_message(self, client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        topic_parts = msg.topic.split("/")
        res_topic = topic_parts[-2]
        last_partition = topic_parts[-1]
        try:
            unknown_command = False
            payload = json.loads(msg.payload.decode())
            command = ""
            match last_partition:
                case "G1":
                    direction = payload.get("dir")
                    if direction is None:
                        raise KeyError("Missing 'dir' key for G1 command.")
                    command = f"{last_partition} {direction}"
                    print("Handling Group G1")
                case "G2":
                    direction = payload.get("dir")
                    pulses = payload.get("pulses")
                    if direction is None or pulses is None:
                        raise KeyError("Missing 'dir' or 'pulses' key for G2 command.")
                    command = f"{last_partition} {direction} {pulses}"
                    print("Handling Group G2")
                case "G3":
                    direction = payload.get("dir")
                    if direction is None:
                        raise KeyError("Missing 'dir' key for G3 command.")
                    command = f"{last_partition} {direction}"
                    print("Handling Group G3")
                case "G4":
                    self.request_id = topic_parts[-2]
                    command = last_partition
                    print("Handling Group G4" + self.request_id)
                case "G5":
                    command = last_partition
                    print("Handling Group G5")
                case "G6":
                    on_off = payload.get("on/off")
                    if on_off is None:
                        raise KeyError("Missing 'on/off' key for G6 command.")
                    command = f"{last_partition} {on_off}"
                    print("Handling Group G6")
                case _:
                    print("Group not recognized")
                    unknown_command = True

def on_message(client, userdata, msg):
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    topic_parts = msg.topic.split('/')
    res_topic = topic_parts[-2]
    last_partition = topic_parts[-1]
    try:
        unknown_command = False
        payload = json.loads(msg.payload.decode())  # Assuming payload is JSON
        command = ""
        match last_partition:
            case "G1":
                dir = payload.get("dir")
                if dir is None:
                    raise KeyError("Missing 'dir' key for G1 command.")
                command = last_partition + " " + dir
                print("Handling Group G1")
            case "G2":
                dir = payload.get("dir")
                duration_ms = payload.get("duration")
                if dir is None or duration_ms is None:
                    raise KeyError("Missing 'dir' or 'duration' key for G2 command.")
                if dir not in {"F", "B"}:
                    raise ValueError("Invalid 'dir' for G2 command. Expected 'F' or 'B'.")
                duration_ms = int(duration_ms)
                if duration_ms < 0 or duration_ms > 10000:
                    raise ValueError("Invalid 'duration' for G2 command. Expected an integer between 0 and 10000.")
                command = f"{last_partition} {dir} T {duration_ms}"
                print("Handling Group G2")
            case "G3":
                dir = payload.get("dir")
                if dir is None:
                    raise KeyError("Missing 'dir' key for G3 command.")
                command = last_partition + " " + dir
                print("Handling Group G3")
            case "G4":
                global request_id
                request_id = (msg.topic).split("/")[-2]
                command = last_partition
                print("Handling Group G4" + request_id)
            case "G5":
                command = last_partition
                print("Handling Group G5")
            case "G6":
                on_off = payload.get("on/off")
                if on_off is None:
                    raise KeyError("Missing 'on/off' key for G6 command.")
                command = last_partition + " " + str(on_off)
                print("Handling Group G6")
            case _:
                print("Group not recognized")
                unknown_command = True

            if not unknown_command:
                if self.ser is None:
                    raise RuntimeError("Serial connection is not available.")

                self.ser.write((command + "\n").encode())
                print(f"Sent to Serial: {command}")
                if last_partition != "G4":
                    response_topic = f"{self.respond_topic}{res_topic}/{last_partition}"
                    response_payload = {}
                    serialized_response = json.dumps(response_payload)
                    client.publish(response_topic, serialized_response, qos=self.qos)
                    print(f"Published trajectory to topic: {response_topic}")

        except json.JSONDecodeError as exc:
            print(f"Failed to decode JSON: {exc}")
        except KeyError as exc:
            print(f"Missing key in payload: {exc}")
        except Exception as exc:
            print(f"An unexpected error occurred while processing the message: {exc}")


    def extract_json(self, data_string):
        pattern = r"(\w+):\s*([\d.]+)"
        matches = re.findall(pattern, data_string)
        return {key: float(value) for key, value in matches}

    def serial_to_mqtt(self):
        while True:
            if self.ser and self.ser.in_waiting > 0:
                try:
                    serial_data = self.ser.readline().decode("utf-8").rstrip()
                    if serial_data:
                        json_dict = self.extract_json(serial_data)
                        if "A" in json_dict and "V" in json_dict:
                            if self._should_publish_telemetry():
                                self.client.publish(self.pub_topic, json.dumps(json_dict), qos=self.qos)
                        elif "START_SENSOR" in json_dict:
                            self.client.publish(
                                self.respond_topic + self.request_id + "/G4",
                                json.dumps(json_dict),
                                qos=self.qos,
                            )
                except (UnicodeDecodeError, ValueError) as exc:
                    print(f"Error reading from serial: {exc}")
                except Exception as exc:
                    print(f"An unexpected error occurred while processing serial data: {exc}")

            time.sleep(0.01)

    def start(self):
        self.client.loop_start()
        self.serial_thread = threading.Thread(target=self.serial_to_mqtt, daemon=True)
        self.serial_thread.start()

    def stop(self):
        if self.ser:
            self.ser.close()
        self.client.loop_stop()
        self.client.disconnect()
