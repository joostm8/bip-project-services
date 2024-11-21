# G2MQTT Serial Interface - README

## Overview
This project is an interface that connects a serial device to an MQTT broker, enabling data transfer between the serial device and MQTT topics. The script listens for incoming MQTT messages, processes them, and sends appropriate commands to the serial device. It also publishes telemetry data from the serial device to specific MQTT topics.

### Features
- Subscribes to MQTT topics to receive commands.
- Publishes telemetry and responses from a serial device to MQTT topics.
- Supports multiple command groups (G1, G2, G3, G4, G5, G6).

## Prerequisites
- Python 3.x
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) library for MQTT communication
- [pyserial](https://pypi.org/project/pyserial/) library for serial communication

## Installation
1. Clone the repository or download the Python script.
2. Install the required Python packages:
   ```sh
   pip install paho-mqtt pyserial
   ```

## Configuration
- **MQTT Broker**: Set the `MQTT_BROKER` and `MQTT_PORT` variables to match your MQTT broker settings.
- **Device ID**: Set the `DEVICE_ID` variable to uniquely identify your device.
- **Serial Port**: Update `SERIAL_PORT` with the appropriate port name (e.g., `COM5` for Windows, `/dev/ttyUSB0` for Linux).
- **Baud Rate**: Set the desired `BAUD_RATE` for serial communication.

## Running the Code
Run the script using Python:
```sh
python G2MQTT.py
```

## MQTT Topics
The following MQTT topics are used by this script:

### 1. Command Topics
- **Subscribe Topic**: `command/bip-server/{DEVICE_ID}/req/#`
  - This topic listens for commands to be executed by the serial device.
  - Replace `{DEVICE_ID}` with your device's unique ID.

#### Command Examples:

##### G1 Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/G1`
- **Payload**:
  ```json
  {
    "dir": "F"
  }
  ```
  - Description: Sends a "G1" command with direction "F" to the serial device.
  - F for forwards, B for backwards.
##### G2 Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/G2`
- **Payload**:
  ```json
  {
    "dir": "B",
    "pulses": 20
  }
  ```
  - The `G2` command moves the conveyor forwards or backwards a certain amount of pulses/steps.
  one pulse is 1/8th of a rotatino of the conveyor's axle.
##### G3 Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/G3`
- **Payload**:
  ```json
  {
    "dir": "F"
  }
  ```
  - The `G3` command moves the conveyor forwards or backwards until the object
  on the conveyor meets the start/end sensor.
##### G4 Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/G4`
- **Payload**: No payload required
  - Description: Sends a "G4" command to the serial device.
  - The `G4` command queries the sensor (start, stop and pulse counter) state.
##### Returns

  `START_SENSOR: [1/0], END_SENSOR [1/0], PULSE_COUNT: [integer]`

##### G5 Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/G5`
- **Payload**: No payload required
  - Description: The `G5` command stops the conveyor.

##### G6 Command
- **Topic**: `command/bip-server/{DEVICE_ID}/req/G6`
- **Payload**:
  ```json
  {
    "on/off": 1
  }
  ```
  - Description: [on/off]: 0 to turn off, any other value to turn on.

### 2. Response Topics
- **Publish Topic**: `command/bip-server/{DEVICE_ID}/res/{request_id}/{command}`
  - The script publishes responses to this topic based on the received command.
  - Example response topic: `command/bip-server/1/res/req/G4`

### 3. Telemetry Topic
- **Publish Topic**: `telemetry/bip-server/{DEVICE_ID}`
  - The script publishes telemetry data received from the serial device to this topic.
  - Example telemetry data:
    ```json
    {
      "A": 5.0,
      "V": 3.5
    }
    ```
  - This output has the shape `A: SX.XX,V: SY.YY`, where S is the optional
minus (-) sign, and the angle and angular velocity are printed with 2
decmial places. 

## Usage
1. Ensure your MQTT broker is running and accessible.
2. Connect your serial device to the specified port.
3. Run the script.
4. Use an MQTT client (e.g., [MQTT Explorer](https://mqtt-explorer.com/)) to publish commands to the appropriate topics and observe responses and telemetry data.

## Error Handling
- The script has built-in error handling to manage issues such as:
  - Invalid JSON payloads: If a command payload cannot be parsed, an error message is printed.
  - Missing keys: If the required keys are missing from the JSON payload, an error message is printed.
  - Serial communication errors: Errors during serial communication are caught and logged.

  