

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

## Running the code

run each file in a separate terminal

      python mqtt_gantry_controller.py
      python mqtt_database_writer.py
      python mqtt_trajectory_generator.py

## Configuration

The scripts get their configuration from `crane-properties.yaml`. For you there is only one important parameter in there, which is `machine id`, which you should set equal to your group number.

## mqtt_trajectory_generator.py interface

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

## mqtt_gantry_controller.py interface

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

## mqtt_database_writer.py interface

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

