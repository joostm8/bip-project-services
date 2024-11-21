from gantry_system.trajectory_generator import TrajectoryGenerator

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

class TrajectoryMQTTWrapper:
    def __init__(self, config_path='config.yaml'):
        # Load the ID from the YAML configuration file
        self.id = load_config(config_path)
        if not self.id:
            raise ValueError("ID not found in configuration file.")

        self.tg = TrajectoryGenerator(config_path)

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
        trajectory_id = topic_parts[-2]
        command_action = topic_parts[-1]

        # Validate if the command is the correct one
        if command_action == "generate-trajectory":
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                start = payload['start']
                stop = payload['stop']
                genmethod = payload['genmethod']

                # Generate the trajectory using a user-defined function
                if genmethod == 'ocp':
                    trajectory = self.tg.generateTrajectory(start, stop)
                else:
                    trajectory = self.tg.generateTrajectoryLQR(start, stop)

                # Publish the generated trajectory to the response topic
                response_topic = f"command/bip-server/{self.id}/res/{trajectory_id}/generate-trajectory"
                serialized_trajectory = pickle.dumps(trajectory)
                client.publish(response_topic, serialized_trajectory, qos=2)
                print(f"Published trajectory to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}")

    def start(self):
        # Start the MQTT loop to listen for messages
        self.client.loop_forever()

if __name__ == "__main__":
    wrapper = TrajectoryMQTTWrapper(config_path="./crane_optimal_control/gantry_system/crane-properties.yaml")
    wrapper.start()

# Serialization Method Explanation
# --------------------------------
# I chose to use `pickle` for serializing the trajectory object. Here are some points for consideration:
#
# **Pickle:**
# - Pros: Efficient and straightforward for serializing Python objects without needing to convert them to another structure.
# - Cons: Not language-agnostic. If other systems (e.g., written in non-Python languages) need to deserialize the message, `pickle` will not be a suitable choice.
#
# **JSON:**
# - Pros: Human-readable and widely supported across different programming languages. Easy to debug.
# - Cons: Less efficient in terms of serialization speed and message size when dealing with more complex or nested data structures like NumPy arrays.
#
# **BSON:**
# - Pros: More efficient than JSON, especially for binary data, and retains some readability. Useful if interoperability is needed but with better performance than JSON.
# - Cons: Still has some overhead compared to `pickle`, and it is less popular than JSON in some environments.
#
# You could use JSON if the trajectory data needs to be shared between different systems or inspected manually, or BSON if you need a compromise between efficiency and interoperability.
