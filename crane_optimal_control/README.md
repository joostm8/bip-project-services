

## Prerequisites
- Python 3.x
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) library for MQTT communication
- [pyserial](https://pypi.org/project/pyserial/) library for serial communication
- [PyYAML](https://pypi.org/project/PyYAML/) library for YAML configuration handling
- [psycopg](https://pypi.org/project/psycopg/) library for PostgreSQL database communication
- [rockit](https://gitlab.kuleuven.be/meco-software/rockit)
## Installation
1. Clone the repository or download the Python script.
2. Install the required Python packages:
   ```sh
   pip install paho-mqtt pyserial PyYAML psycopg[binary] rockit-meco pytinamic
   ```

## Configuration
- **MQTT Broker**: Set the `MQTT_BROKER` and `MQTT_PORT` variables to match your MQTT broker settings.
- **Device ID**: Set the `DEVICE_ID` variable to uniquely identify your device.
- **Serial Port**: Update `SERIAL_PORT` with the appropriate port name (e.g., `COM5` for Windows, `/dev/ttyUSB0` for Linux).
- **Baud Rate**: Set the desired `BAUD_RATE` for serial communication.
- **Trajectory Generation Configuration**: Update the `config.yaml` file to include the machine ID and other relevant properties.
- **Gantry System Configuration**: Update the `config.yaml` file with machine properties for gantry system control.
- **Database Configuration**: Update the `config.yaml` file with properties such as database address, name, user, and password for storing trajectories and measurements.

##### Generate Trajectory Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/generate-trajectory`
- **Payload**:
  ```json
  {
    "start": [0, 0, 0],
    "stop": [10, 10, 10],
    "genmethod": "ocp"
  }
  ```
  - Description: Sends a command to generate a trajectory between the start and stop points using the specified method (`ocp` or `lqr`).

##### Gantry Hoist Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/hoist`
- **Payload**:
  ```json
  {
    "height": 5
  }
  ```
  - Description: Sends a command to hoist the gantry to the specified height.

##### Gantry Move Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/move`
- **Payload**:
  ```json
  {
    "position": [5, 5, 5]
  }
  ```
  - Description: Sends a command to move the gantry to the specified position.

##### Gantry Simple Move Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/simplemove`
- **Payload**:
  ```json
  {
    "position": [3, 3, 3]
  }
  ```
  - Description: Sends a command to move the gantry to the specified position without logging.

##### Store Trajectory Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/store-trajectory`
- **Payload**: Serialized trajectory data (using `pickle`)
  - Description: Sends a command to store a generated trajectory in the database.

##### Store Measurement Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/store-measurement`
- **Payload**: Serialized measurement data (using `pickle`)
  - Description: Sends a command to store a measurement in the database.

### 2. Response Topics
- **Publish Topic**: `command/bip-server/{DEVICE_ID}/res/{request_id}/{command}`
  - The script publishes responses to this topic based on the received command.
  - Example response topic: `command/bip-server/1/res/req/G4`

- **Trajectory Response Topic**: `command/bip-server/{DEVICE_ID}/res/{trajectory_id}/generate-trajectory`
  - The generated trajectory is serialized and published to this topic.
  - Example response: Serialized trajectory data.

- **Gantry Hoist Response Topic**: `command/bip-server/{DEVICE_ID}/res/{request_id}/hoist`
  - Example response:
    ```json
    {
      "height": 5
    }
    ```

- **Gantry Move Response Topic**: `command/bip-server/{DEVICE_ID}/res/{request_id}/move`
  - Example response:
    ```json
    {
      "position": [5, 5, 5]
    }
    ```

- **Gantry Simple Move Response Topic**: `command/bip-server/{DEVICE_ID}/res/{request_id}/simplemove`
  - Example response:
    ```json
    {
      "position": [3, 3, 3]
    }
    ```

- **Store Trajectory Response Topic**: `command/bip-server/{DEVICE_ID}/res/store-trajectory/200`
  - Description: Confirms successful storage of the trajectory in the database.

- **Store Measurement Response Topic**: `command/bip-server/{DEVICE_ID}/res/store-measurement/200`
  - Description: Confirms successful storage of the measurement in the database.
