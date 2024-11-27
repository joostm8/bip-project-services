"""
Teacher solution to the bip case study.
Assumes all mqtt microservices have been started:
- mqtt_database_writer.py
- mqtt_gantry_controller.py
- mqtt_trajectory_generator.py
- GtoMQTT
- mqtt_aruco_detector
- shipsimulationmain.py
...

The script then attemps to load containers onto the ship in order.
Containers that are not in the shipping manifest or that arrive out of
order are rejected.
"""

import json
import uuid
import paho.mqtt.client as mqtt
from threading import Event
from time import sleep

MOVE_HEIGHT = 0.2
PICKUP_HEIGHT = 0.073
PICKUP_POSITION = 0.6
CONTAINER_HEIGHT = 0.025
SHIP_HEIGHT = 0
QUAY_HEIGHT = 0
SHIP_POSITIONS = [0.08, 0.04, 0]
QUAY_POSITIONS = [0.28, 0.24, 0.2]


class BipTeacherSolution:

    def __init__(self, id = 1):
        self.id = 1 # used in mqtt topics
        self.response_id = str(uuid.uuid4())  # Generate a random id that associates all responses with this script
        self.response_event = Event()
        self.G4_event = Event()
        self.aruco_event = Event()
        self.G2_event = Event()
        self.G3_event = Event()
        self.hoist_event = Event()
        self.move_event = Event()
        self.G6_event = Event()
        self.G4_answer = None
        self.aruco_answer = None
        self.hoist_answer = None
        self.move_answer = None

        # placeholder containers and loading order.
        self.loadingorder = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.container_positions = [(i, j) for i in range(3) for j in range(5)]

        ## setup mqtt client, subscribe to all needed response topics.
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()

        ## placeholder 

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the response topics
        topic = f"command/bip-server/{self.id}/res/{self.response_id}/#"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")
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
            # Deserialize the trajectory
            print(f"Received trajectory on topic: {msg.topic}")
            received_response = json.loads(msg.payload)
            print(f"{received_response}")
            if command_action == "G4":
                self.G4_answer = received_response
                self.G4_event.set()
            elif command_action == "G2":
                self.G2_event.set()
            elif command_action == "G3":
                self.G3_event.set()
            elif command_action == "aruco-id":
                print(received_response)
                self.aruco_answer = received_response
                self.aruco_event.set()
            elif command_action == "hoist":
                self.hoist_answer = received_response
                self.hoist_event.set()
            elif command_action == "move" or command_action == "simplemove":
                self.move_answer = received_response
                self.move_event.set()
            elif command_action == "G6":
                self.G6_event.set()
            else:
                self.response_event.set()
        except Exception as e:
            print(f"Error processing message: {e}")

    def checkForContainerArrival(self):
        # Publish the request to check the sensor state of the conveyor
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/G4"
        payload = {}
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.G4_event.wait()
        self.G6_event.clear()
        # expected response is the G4 command, which is a json with the fields
        # START_SENSOR
        # END_SENSOR
        # PULSE_COUNT
        # it gets set in the on_message function
        print(self.G4_answer)
        return not self.G4_answer["END_SENSOR"]

    def moveContainerToScanArea(self):
        # Publish the request to move the conveyor to the scan area
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/G2"
        payload = {
            "dir":"B",
            "pulses":27
        }
        # about 25 pulses backwards is sufficient to reach the sensor
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.G2_event.wait()
        self.G2_event.clear()
        sleep(2) # command returns immediately, belt takes some time to reach that point.

    def scanContainer(self):
        # Publish the request to check the sensor state of the conveyor
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/aruco-id"
        payload = {}
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.aruco_event.wait()
        self.aruco_event.clear()
        # expected response is the aruco json, which contains a list of ids
        # id:[...]
        # it gets set in the on_message function
        if not self.aruco_answer["id"]:
            # list is empty, no container was scanned
            return None
        else:
            # list is not empty, return the first id
            return self.aruco_answer["id"][0]

    def rejectContainer(self):
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/G3"
        payload = {
            "dir":"F",
        }
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.G3_event.wait()
        self.G3_event.clear()

    def acceptContainer(self):
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/G3"
        payload = {
            "dir":"B",
        }
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.G3_event.wait()
        self.G3_event.clear()
        sleep(1)

    def hoistCrane(self, height):
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/hoist"
        payload = {
            "height":height,
        }
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.hoist_event.wait()
        self.hoist_event.clear()
        # the hoisting function publishes the final height back
        # can be used as sanity check to see that the height was actually reached.
        return self.hoist_answer["height"]

    def moveCrane(self, position):
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/move"
        payload = {
            "position":position,
        }
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.move_event.wait()
        self.move_event.clear()
        # the hoisting function publishes the final height back
        # can be used as sanity check to see that the height was actually reached.
        return self.move_answer["position"]

    def electromagnet(self, onOff=True):
        request_topic = f"command/bip-server/{self.id}/req/{self.response_id}/G6"
        payload = {
            "on/off":1 if onOff else 0,
        }
        self.client.publish(request_topic, json.dumps(payload), qos=2)
        print(f"Published request to topic: {request_topic}")
        print("Waiting for crane response...")
        self.G6_event.wait()
        self.G6_event.clear()

    def updateShipSimulation(self, container_id, pos):
        request_topic = f"control/ship/{self.id}/containers/incoming"
        payload ={
            "container": {
                "weight": 20000,
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

    def removeFromLoadingOrder(self):
        self.loadingorder = self.loadingorder[1:]

    def clearAllEvents(self):
        self.G4_event.clear()
        self.aruco_event.clear()
        self.G2_event.clear()
        self.G3_event.clear()
        self.hoist_event.clear()
        self.move_event.clear()
        self.G6_event.clear()
        
if __name__ == "__main__":
    sol = BipTeacherSolution()
    
    while True:
        sol.clearAllEvents()
        while not sol.checkForContainerArrival():
            print("No container has arrived, sleeping for 1 second")
            sleep(1)
        # input("pres enter when a container has been loaded:")
        print("container has arrived, loading it to the scanning station")
        sol.moveContainerToScanArea()
        print("arrived ad scanning station, scanning...")
        scanned_id = sol.scanContainer()
        while not scanned_id:
            scanned_id = sol.scanContainer()
            print("no id was scanned, try rotating the container")
            sleep(1)
        print(f"Scanned container with id: {scanned_id}")
        if scanned_id == sol.loadingorder[0]:
            print("Container can be loaded")
            print(f"Loading position is{sol.container_positions[scanned_id]}")
            sol.acceptContainer()
            container_position = sol.container_positions[scanned_id-1]
            sol.hoistCrane(MOVE_HEIGHT)
            sol.moveCrane(PICKUP_POSITION)
            sol.hoistCrane(PICKUP_HEIGHT)
            sol.electromagnet(True)
            sleep(1)
            sol.hoistCrane(MOVE_HEIGHT)
            sol.moveCrane(SHIP_POSITIONS[container_position[0]])
            sol.hoistCrane(SHIP_HEIGHT + CONTAINER_HEIGHT*(container_position[1]+1))
            sol.electromagnet(False)
            sol.hoistCrane(MOVE_HEIGHT)
            # container should now have been placed down in on the ship,
            # this means we should notify the simulation
            # sol.updateShipSimulation(scanned_id, container_position)
            sol.removeFromLoadingOrder()
        elif scanned_id in sol.loadingorder:
            # id in loading, but too early
            print(f"Container {scanned_id} is in the loading list, but would be loaded too early, please present it again later")
            sol.rejectContainer()
            input("Please unload the container and press any key to continue...")
        else:
            print(f"Container {scanned_id} is not in the loading manifest and is rejected")
            sol.rejectContainer()
            input("Please unload the container and press any key to continue...")