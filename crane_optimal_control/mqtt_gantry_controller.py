from gantry_system.gantry_controller import PhysicalGantryController, MockGantryController

import yaml
import json
import paho.mqtt.client as mqtt
import pickle
import os

# Load the ID from the YAML configuration file
def load_config(config_file="config.yaml"):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config.get("machine id")

class ControllerMQTTWrapper:
    def __init__(self, config_path='config.yaml', mock = False):
        # Load the ID from the YAML configuration file
        self.id = load_config(config_path)
        if not self.id:
            raise ValueError("ID not found in configuration file.")
        if mock:
            self.ctl = MockGantryController(config_path)
        else:
            self.ctl = PhysicalGantryController(config_path)

        # MQTT Client setup
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the command topic
        topic = f"command/bip-server/{self.id}/req/#"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

    def on_message(self, client, userdata, msg):
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
                final_height = self.ctl.hoist(height)

                # Respond with the final height to the response topic
                response_topic = f"command/bip-server/{self.id}/res/{res_topic}/hoist"
                payload = {
                    "height" : final_height
                }
                serialized_height = json.dumps(payload)
                client.publish(response_topic, serialized_height)
                print(f"Published height to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}")
        if command_action == "move":
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                position = payload["position"]

                # move to that position
                final_position = self.ctl.mqttMoveWithLog(position)

                # Respond with the final position to the response topic
                response_topic = f"command/bip-server/{self.id}/res/{res_topic}/move"
                payload = {
                    "position" : final_position
                }
                serialized_trajectory = json.dumps(payload)
                client.publish(response_topic, serialized_trajectory)
                print(f"Published trajectory to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}")
        if command_action == "simplemove":
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                position = payload["position"]

                # move to that position
                final_position = self.ctl.simpleMove(position)

                # Respond with the final position to the response topic
                response_topic = f"command/bip-server/{self.id}/res/{res_topic}/simplemove"
                payload = {
                    "position" : final_position
                }
                serialized_trajectory = json.dumps(payload)
                client.publish(response_topic, serialized_trajectory)
                print(f"Published trajectory to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}")

    def start(self):
        # Start the MQTT loop to listen for messages
        self.client.loop_forever()

if __name__ == "__main__":
    wrapper = ControllerMQTTWrapper("./crane_optimal_control/gantry_system/crane-properties.yaml", mock= True)
    wrapper.start()