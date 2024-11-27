

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
   pip install paho-mqtt pyserial PyYAML psycopg[binary] rockit-meco pytrinamic
   ```

## Configuration
- **MQTT Broker**: Set the `MQTT_BROKER` and `MQTT_PORT` variables to match your MQTT broker settings.
- **Device ID**: Set the `DEVICE_ID` variable to uniquely identify your device.
- **Serial Port**: Update `SERIAL_PORT` with the appropriate port name (e.g., `COM5` for Windows, `/dev/ttyUSB0` for Linux).
- **Baud Rate**: Set the desired `BAUD_RATE` for serial communication.
- **Trajectory Generation Configuration**: Update the `config.yaml` file to include the machine ID and other relevant properties.
- **Gantry System Configuration**: Update the `config.yaml` file with machine properties for gantry system control.
- **Database Configuration**: Update the `config.yaml` file with properties such as database address, name, user, and password for storing trajectories and measurements.

#### Generate Trajectory Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/{trajectory-id}/generate-trajectory`
- **Payload**:
  ```json
  {
    "start": 0,
    "stop": 10,
    "genmethod": "ocp"
  }
  ```
   - Description: Sends a command to generate a trajectory between the start and stop points using the specified method (`ocp` or `lqr`).
- **Response Topic**: `command/bip-server/{DEVICE_ID}/res/{trajectory-id}/generate-trajectory`
- **Response Payload**: pickled trajectory.

#### Gantry Hoist Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/{response-id}/hoist`
- **Payload**:
  ```json
  {
    "height": 5
  }
  ```
   - Description: Sends a command to hoist the gantry to the specified height.
- **Response Topic**: `command/bip-server/{DEVICE_ID}/req/{response-id}/hoist`
- **Response Payload**:
   ```json
   {
    "height": <the actual height>
   }
   ```

#### Gantry Move Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/{response-id}/move`
- **Payload**:
  ```json
  {
    "position": 5
  }
  ```
   - Description: Sends a command to move the gantry to the specified position.
- **Reponse Topic**: `command/bip-server/{DEVICE_ID}/res/{response-id}/move`
- **Response Payload**:
  ```json
  {
    "position": <the actual position>
  }
  ```

#### Gantry Simple Move Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/simplemove`
- **Payload**:
  ```json
  {
    "position": 3
  }
  ```
   - Description: Sends a command to move the gantry to the specified position without generating an optimal move trajectory. This just relies on the gantry's onboard controller.
- **Reponse Topic**: `command/bip-server/{DEVICE_ID}/res/{response-id}/move`
- **Response Payload**:
  ```json
  {
    "position": <the actual position>
  }
  ```

#### Store Trajectory Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/store-trajectory`
- **Payload**: Serialized trajectory data (using `pickle`)
  - Description: Sends a command to store a generated trajectory in the database.
- **Response Topic**: `command/bip-server/{DEVICE_ID}/res/store-trajectory/200`
  - Description: Confirms successful storage of the trajectory in the database.

#### Store Measurement Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/store-measurement`
- **Payload**: Serialized measurement data (using `pickle`)
  - Description: Sends a command to store a measurement in the database.
- **Response Topic**: `command/bip-server/{DEVICE_ID}/res/store-measurement/200`
  - Description: Confirms successful storage of the measurement in the database.

