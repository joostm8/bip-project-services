# ArUco Identification MQTT Interface

## MQTT Topics

For students: this service is already running in the lab setup.
Use this page to see which topic to call and what response to expect.

All topics follow `{base_topic}/{id}/...`.

- `{base_topic}` comes from `mqtt.base_topic`
- `{id}` is `mqtt.username`

## Commands

### Request detected ArUco IDs

- **Request topic**: `{base_topic}/{id}/req/{response-id}/aruco-id`
- **Payload**: none required
- **Response topic**: `{base_topic}/{id}/res/{response-id}/aruco-id`
- **Response payload**:
  ```json
  {
    "id": [1, 5, 12]
  }
  ```

If no markers are visible, the response is:

```json
{
  "id": []
}
```

## Running locally

Only use this section if you want to run or debug the service yourself.

### Prerequisites

- Python 3.x
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) for MQTT communication
- [OpenCV](https://opencv.org/get-started/) for computer vision and ArUco markers

### Installation

```sh
pip install paho-mqtt opencv-python
```

### Run command

```sh
python examples/aruco_identification/run_mqtt_aruco_detector.py
```

### Configuration

All settings are read from `config.yaml`:

```yaml
mqtt:
  host: <broker address>
  port: 8883
  username: <your id>
  password: <password>
  ca_cert_path: <path to CA certificate, optional>
  base_topic: bip/mqtt-lab
  qos: 2
  keepalive: 60

cam:
  cam_id: 0
  preview: true
```

Useful helpers:

- List cameras: `examples/aruco_identification/list_cameras.py`
- Generate ArUco markers: `examples/aruco_identification/marker_generation.py`


