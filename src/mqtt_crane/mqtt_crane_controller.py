from gantrylib.gantry_controller import PhysicalGantryController, MockGantryController

import yaml
import json
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import MQTTErrorCode

def load_config(config_file="config.yaml"):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config or {}

class MQTTCraneController:
    def __init__(self, config_path='config.yaml', mock = False):
        self.config = load_config(config_path)
        self.id = self.config.get("machine_id")
        if not self.id:
            raise ValueError("ID not found in configuration file.")

        mqtt_cfg = self.config.get("mqtt")
        if mqtt_cfg is None:
            raise ValueError("'mqtt' section not found in configuration file.")

        motion_cfg = self.config.get("mqtt_motion")
        if motion_cfg is None:
            raise ValueError("'mqtt_motion' section not found in configuration file.")

        self.broker_host = mqtt_cfg.get("host", "localhost")
        self.broker_port = int(mqtt_cfg.get("port", 1883))
        self.username = mqtt_cfg.get("username")
        self.password = mqtt_cfg.get("password")
        self.ca_cert_path = mqtt_cfg.get("ca_cert_path")
        self.base_topic = mqtt_cfg.get("base_topic", "bip/mqtt-lab")
        self.qos = int(mqtt_cfg.get("qos", 2))
        self.keepalive = int(mqtt_cfg.get("keepalive", 60))
        self.default_cart_velocity = float(motion_cfg.get("default_cart_velocity", 100))
        self.default_hoist_velocity = float(motion_cfg.get("default_hoist_velocity", 40))
        self.movement_tolerance = float(motion_cfg.get("movement_tolerance", 1))
        self.movement_timeout_s = float(motion_cfg.get("movement_timeout_s", 20.0))
        self.movement_poll_interval_s = float(motion_cfg.get("movement_poll_interval_s", 0.1))

        if mock:
            self.ctl = MockGantryController(self.config)
        else:
            self.ctl = PhysicalGantryController(self.config)

        # MQTT Client setup
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.ca_cert_path:
            self.client.tls_set(ca_certs=self.ca_cert_path)
        if self.username:
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_host, self.broker_port, self.keepalive)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with reason code {reason_code}")
        # Subscribe to the command topic
        topic = f"{self.base_topic}/{self.username}/req/#"
        (result, mid) = client.subscribe(topic, qos=self.qos)
        if result == MQTTErrorCode.MQTT_ERR_SUCCESS:
            print(f"Subscribed to topic: {topic}")
        else:
            print(f"Subscription unsuccessful to topic: {topic}")

    def _move_cart(self, position, velocity):
        crane = self.ctl.crane
        if crane and hasattr(crane, "moveCartPosition"):
            crane.moveCartPosition(position, velocity)
            if hasattr(crane, "getState"):
                return self._wait_for_position(
                    axis="cart",
                    target=position,
                    timeout_s=self.movement_timeout_s,
                    poll_interval_s=self.movement_poll_interval_s,
                )
            return position
        if hasattr(self.ctl, "simpleMove"):
            return self.ctl.simpleMove(position)
        return self.ctl.mqttMoveWithLog(position)

    def _move_hoist(self, height, velocity):
        crane = self.ctl.crane
        if crane and hasattr(crane, "moveHoistPosition"):
            crane.moveHoistPosition(height, velocity)
            if hasattr(crane, "getState"):
                return self._wait_for_position(
                    axis="hoist",
                    target=height,
                    timeout_s=self.movement_timeout_s,
                    poll_interval_s=self.movement_poll_interval_s,
                )
            return height
        return self.ctl.hoist(height)

    def _get_axis_position(self, axis):
        if not hasattr(self.ctl, "crane") or not self.ctl.crane or not hasattr(self.ctl.crane, "getState"):
            raise RuntimeError("Crane state is unavailable for completion check.")

        state = self.ctl.crane.getState()
        if axis == "cart":
            return state[0]
        if axis == "hoist":
            return state[2]
        raise ValueError(f"Unsupported axis: {axis}")

    def _wait_for_position(self, axis, target, timeout_s, poll_interval_s):
        deadline = time.monotonic() + timeout_s
        last_position = self._get_axis_position(axis)

        while time.monotonic() < deadline:
            last_position = self._get_axis_position(axis)
            if abs(last_position - target) <= self.movement_tolerance:
                return last_position
            time.sleep(poll_interval_s)

        raise TimeoutError(
            f"Timed out waiting for {axis} movement to complete. "
            f"target={target}, last_position={last_position}"
        )

    def on_message(self, client, userdata, msg):
        print(f"received message {msg}")
        # Parse the topic to extract the trajectory-id
        topic_parts = msg.topic.split('/')
        res_topic = topic_parts[-2]
        command_action = topic_parts[-1]

        # Validate if the command is the correct one
        if command_action == "hoist":
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                height = payload['height']

                # hoist to the height
                final_height = self._move_hoist(height, self.default_hoist_velocity)
                result = "success"
            except TimeoutError as e:
                print(f"Timeout processing message: {e}")
                final_height = self._get_axis_position("hoist")
                result = "timeout"
            except Exception as e:
                print(f"Error processing message: {e}")
                return

                # Respond with the final height to the response topic
            response_topic = f"{self.base_topic}/{self.username}/res/{res_topic}/hoist"
            payload = {
                "height": final_height,
                "result": result
            }
            serialized_height = json.dumps(payload)
            client.publish(response_topic, serialized_height, qos=self.qos)
            print(f"Published height to topic: {response_topic}")
        if command_action == "move":
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                position = payload["position"]

                # move to that position
                final_position = self._move_cart(position, self.default_cart_velocity)
                result = "success"
            except TimeoutError as e:
                print(f"Timeout processing message: {e}")
                final_position = self._get_axis_position("cart")
                result = "timeout"
            except Exception as e:
                print(f"Error processing message: {e}")
                return

                # Respond with the final position to the response topic
            response_topic = f"{self.base_topic}/{self.username}/res/{res_topic}/move"
            payload = {
                "position": final_position,
                "result": result
            }
            serialized_trajectory = json.dumps(payload)
            client.publish(response_topic, serialized_trajectory, qos=self.qos)
            print(f"Published trajectory to topic: {response_topic}")
        if command_action == "simplemove":
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                position = payload["position"]

                # move to that position
                final_position = self._move_cart(position, self.default_cart_velocity)
                result = "success"
            except TimeoutError as e:
                print(f"Timeout processing message: {e}")
                final_position = self._get_axis_position("cart")
                result = "timeout"
            except Exception as e:
                print(f"Error processing message: {e}")
                return

                # Respond with the final position to the response topic
            response_topic = f"{self.base_topic}/{self.username}/res/{res_topic}/simplemove"
            payload = {
                "position": final_position,
                "result": result
            }
            serialized_trajectory = json.dumps(payload)
            client.publish(response_topic, serialized_trajectory, qos=self.qos)
            print(f"Published trajectory to topic: {response_topic}")

    def start(self):
        # Start the MQTT loop to listen for messages
        self.client.loop_forever()
