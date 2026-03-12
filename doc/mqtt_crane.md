
# MQTT Crane Interface

For students: these services are already running in the lab setup.
Use this page to find the MQTT topics and payloads.

## run_mqtt_gantry_controller.py - MQTTCraneController

Controls physical movement of the crane cart and hoist.

All topics use the pattern `{base_topic}/{username}/...`.

### Hoist

- **Request topic**: `{base_topic}/{username}/req/{response-id}/hoist`
- **Payload**:
  ```json
  { "height": 150 }
  ```
- **Response topic**: `{base_topic}/{username}/res/{response-id}/hoist`
- **Response payload**:
  ```json
  { "height": 151.3, "result": "success" }
  ```
  `result` is `"success"` or `"timeout"`.

### Move cart (optimal trajectory)

- **Request topic**: `{base_topic}/{username}/req/{response-id}/move`
- **Payload**:
  ```json
  { "position": 200 }
  ```
- **Response topic**: `{base_topic}/{username}/res/{response-id}/move`
- **Response payload**:
  ```json
  { "position": 199.8, "result": "success" }
  ```

### Move cart (simple, no trajectory)

- **Request topic**: `{base_topic}/{username}/req/{response-id}/simplemove`
- **Payload**:
  ```json
  { "position": 200 }
  ```
- **Response topic**: `{base_topic}/{username}/res/{response-id}/simplemove`
- **Response payload**:
  ```json
  { "position": 199.8, "result": "success" }
  ```
  Uses the crane's onboard controller directly, without computing an optimal trajectory first.

## run_mqtt_trajectory_generator.py - TrajectoryMQTTWrapper

Generates trajectories when requested.

Topics use the pattern `command/bip-server/{machine_id}/...`.

### Generate trajectory

- **Request topic**: `command/bip-server/{machine_id}/req/{trajectory-id}/generate-trajectory`
- **Payload**:
  ```json
  { "start": 0, "stop": 200, "genmethod": "ocp" }
  ```
  `genmethod`: `"ocp"` (optimal control) or `"lqr"`.
- **Response topic**: `command/bip-server/{machine_id}/res/{trajectory-id}/generate-trajectory`
- **Response payload**: pickled trajectory object (use `pickle.loads(payload)` to deserialize).

## run_mqtt_database_writer.py - DatabaseMQTTWrapper

Stores trajectories and measurements in a PostgreSQL database.

Topics use the pattern `command/bip-server/{machine_id}/...`.

### Store trajectory

- **Request topic**: `command/bip-server/{machine_id}/req/{run-id}/store-trajectory`
- **Payload**: pickled trajectory (as returned by the trajectory generator).
- **Response topic**: `command/bip-server/{machine_id}/res/store-trajectory/200`
- **Response**: empty. Receiving this response confirms successful storage.

### Store measurement

- **Request topic**: `command/bip-server/{machine_id}/req/{run-id}/store-measurement`
- **Payload**: pickled measurement tuple `(timestamps, x, v, a, theta, omega)`.
- **Response topic**: `command/bip-server/{machine_id}/res/store-measurement/200`
- **Response**: empty. Receiving this response confirms successful storage.

## Running locally

Only use this section if you want to run or debug the services yourself.

### Prerequisites

- Python 3.x
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) for MQTT communication
- [PyYAML](https://pypi.org/project/PyYAML/) for configuration
- [psycopg](https://pypi.org/project/psycopg/) for PostgreSQL database communication
- [rockit](https://gitlab.kuleuven.be/meco-software/rockit) toolbox for optimal trajectory generation

### Installation

```sh
pip install paho-mqtt PyYAML psycopg[binary] rockit-meco pytrinamic
```

### Run commands

Run each service in a separate terminal:

```sh
python examples/crane_optimal_control/run_mqtt_gantry_controller.py
python examples/crane_optimal_control/run_mqtt_database_writer.py
python examples/crane_optimal_control/run_mqtt_trajectory_generator.py
```

### Configuration

All services read from `config.yaml`. Key fields:

```yaml
machine_id: 1

mqtt:
  host: <broker address>
  port: 8883
  username: <username>
  password: <password>
  ca_cert_path: <CA certificate path, optional>
  base_topic: bip/mqtt-lab
  qos: 2
  keepalive: 60

mqtt_motion:
  default_cart_velocity: 100
  default_hoist_velocity: 40
```


