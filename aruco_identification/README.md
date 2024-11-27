## Prerequisites

- Python 3.x
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) library for MQTT communication
- [OpenCV](https://opencv.org/get-started/) for computer vision and the aruco markers.

## Installation

    pip install paho-mqtt opencv-python

## Running the code

In a terminal, run

    python mqtt_aruco_detector.py

## configuration

Set `GROUP_ID` on top of the file equal to your group id. \
You might have to change `CAM_ID` to the ID of your camera. Usually 0 is your built-in webcam that can be used for testing.
To list available camera ids, you can execute `list_cameras.py`.

# mqtt interface

#### Generate Trajectory Command
- **Topic**: `command/bip-server/{GROUP_ID}/req/{response-id}/aruco-id`
- **Payload**: not needed
   - Description: Requests the identifier to return the list of identified ids.
- **Response Topic**: `command/bip-server/{GROUP_ID}/res/{response-id}/aruco-id`
- **Response Payload**:
  ```json
  {
    "id": <list of identified ids, empty list when none>
  }
  ```
  

