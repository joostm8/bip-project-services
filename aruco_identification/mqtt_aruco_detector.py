import json
import pickle
import paho.mqtt.client as mqtt
import cv2
import numpy as np
from aruco_detector import ArucoDetector

GROUP_ID = 1
CAM_ID = 0

class ArucoMQTTService:
    def __init__(self, id = 1, detector = None):
        if detector is None:
            raise TypeError('Please provide a valid detector.')
        self.detector = detector
        self.id = id

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)
    
    # Callback when connected to MQTT broker
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the request topic
        topic = f"command/bip-server/{self.id}/req/#"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

    def on_message(self, client, userdata, msg):
        # Parse the topic to extract the trajectory-id
        topic_parts = msg.topic.split('/')
        res_topic = topic_parts[-2]
        command_action = topic_parts[-1]

        # Validate if the command is the correct one
        if command_action == "aruco-id":
            try:
                marker_id, _ = self.detector.detect()

                # Prepare the response message
                # respond even if id is none.
                if marker_id is not None:
                    print(marker_id)
                    marker_id = [int(i) for id in ids for i in id]
                    response = f"Marker ID: {[i for id in ids for i in id]}"
                else:
                    response = "No marker detected"
                    marker_id = []

                # Publish the response to the response topic
                # Respond with the final position to the response topic
                response_topic = f"command/bip-server/{self.id}/res/{res_topic}/aruco-id"
                payload = {
                    "id": marker_id
                }
                print(type(marker_id))
                print(payload)
                serialized_marker_ids = json.dumps(payload)
                client.publish(response_topic, serialized_marker_ids, qos =2 )
                print(f"Published trajectory to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}") 
                # publish something anyway
                response_topic = f"command/bip-server/{self.id}/res/{res_topic}/aruco-id"
                payload = {
                    "id": []
                }
                serialized_marker_ids = json.dumps(payload)
                client.publish(response_topic, serialized_marker_ids, qos =2 )
                print(f"Published trajectory to topic: {response_topic}")


    # Start the MQTT client loop
    def start(self):
        # Start the MQTT loop to listen for messages
        self.client.loop_start()

    # Clean up resources
    def stop(self):
        self.cap.release()
        self.client.loop_stop()

# Main function to run the service
if __name__ == "__main__":
    # Initialize and start the Aruco MQTT service
    detector = ArucoDetector(show_rejected=True, cam_id=CAM_ID)

    aruco_service = ArucoMQTTService(detector=detector, id = GROUP_ID)
    aruco_service.start()

    while True:
        ids, frame = detector.detect()
        cv2.imshow("out", frame)
        # Exit if 'ESC' is pressed
        key = cv2.waitKey(10)
        if key == 27:  # ASCII for ESC key
            break
    print("Stopping Aruco MQTT service.")
    aruco_service.stop()
    detector.release()
