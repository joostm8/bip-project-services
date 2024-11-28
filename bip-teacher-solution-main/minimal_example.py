"""
Very minimal example of initializing a new ship simulation,
then querying the database for a container in slot 0,
finding out the weight, and updating the simulation with that container.

Utilizes the retain function of MQTT to obtain the ship simulation initial state
regardless of the startup order of the simulator/example.

Needs shipsimulationmain.py to be running.
"""

import json
from threading import Event
import paho.mqtt.client as mqtt
from direct_database_writer import DirectDatabaseWriter
from time import sleep


class MinimalExample():
    
    def __init__(self, id = 1):
        self.id = 1
        self.response_event = Event()
        self.response = None

        ## setup mqtt client, subscribe to all needed response topics.
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the response topics
        topic = f"telemetry/ship/{self.id}/#"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

    def on_message(self, client, userdata, msg):
        """
        Executed when a message is received on any of the subscribed topics
        Used to get the message payload, and set the event that is blocking the function call.
        """
        # Parse the topic to extract 
        topic_parts = msg.topic.split('/')
        res_topic = topic_parts[-2]
        command_action = topic_parts[-1]

        try:
            if topic_parts[0] == "telemetry":
                self.response = json.loads(msg.payload)
                print(f"Received response on topic: {msg.topic}")
                self.response_event.set()
        except Exception as e:
            print(f"Error processing message: {e}")
        
    def updateShipSimulation(self, container_id, pos, weight):
        request_topic = f"control/ship/{self.id}/containers/incoming"
        payload ={
            "container": {
                "weight": weight,
                "container_id": f"CONT{container_id}"
                },
            "position": {
                "x": pos[0],
                "y": pos[1]
            }
        }
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.response_event.wait()
        self.response_event.clear()
        print(self.response)

    def waitForRetained(self):
        example.response_event.wait()
        example.response_event.clear()
        print(self.response)

if __name__ == "__main__":
    example = MinimalExample(id=1)
    # this is a little bit of a special case: shipsimulationmain.py publishes the initial state
    # just to make sure the example can still get that state, it is retained.
    # after connecting, we wait for this retained message to arrive.
    # afterwards, we can continue like usual.
    example.waitForRetained()
    dbw = DirectDatabaseWriter(1)
    dbw.setShipRoll(example.response["heel_angle"])
    dbw.setShipDraft(example.response["draught"])
    # add a sleep here to see the change in the dashboard.

    container_id = dbw.getContainerInShipSlot(0)
    container_pos = dbw.getShipSlotPosition(0)
    weight = dbw.getContainerWeight(container_id)
    example.updateShipSimulation(container_id, container_pos, weight)
    dbw.setShipRoll(example.response["heel_angle"])
    dbw.setShipDraft(example.response["draught"])
