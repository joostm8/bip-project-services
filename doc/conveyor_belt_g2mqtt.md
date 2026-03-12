# Conveyor Belt G2MQTT Interface

The conveyor belt has no mock interface, so you will likely not use it directly in your project. It is included here for completeness.

## MQTT Topics

For students: this service is already running in the lab setup.
Use this page to find the topic and payload definitions.

| Direction | Topic pattern |
|-----------|---------------|
| Subscribe (commands) | `{base_topic}/{id}/req/#` |
| Publish (responses)  | `{base_topic}/{id}/res/{request-id}/{command}` |
| Publish (telemetry)  | `{base_topic}/{id}/telemetry` |

## Commands

### G1 – Move continuously

```json
{ "dir": "F" }
```

`dir`: `"F"` (forward) or `"B"` (backward). Runs until stopped or until a sensor is reached.

### G2 – Move for a fixed duration

```json
{ "dir": "F", "duration": 500 }
```

`duration`: time in milliseconds, range `0` to `10000`.

### G3 – Move until sensor

```json
{ "dir": "F" }
```

Moves the conveyor until the start or end sensor is triggered.

### G4 – Query sensor state

No payload required. The response is published to `{base_topic}/{id}/res/{request-id}/G4`:

```json
{ "START_SENSOR": 0, "END_SENSOR": 1, "PULSE_COUNT": 42 }
```

### G5 – Stop

No payload required. Stops the conveyor immediately.

### G6 – Toggle output (e.g. light)

```json
{ "on/off": 1 }
```

`0` = off, any other value = on.

## Telemetry

Published periodically to `{base_topic}/{id}/telemetry`:

```json
{ "A": 2.75, "V": 1.33 }
```

`A` = angle, `V` = angular velocity.

## Running locally

Only use this section if you want to run or debug the service yourself.

### Prerequisites

- Python 3.x
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) for MQTT communication
- [pyserial](https://pypi.org/project/pyserial/) for serial communication

### Installation

```sh
pip install paho-mqtt pyserial
```

### Run command

```sh
python examples/conveyor_belt_g2mqtt/run_g_to_mqtt.py
```

### Configuration

All settings are read from `config.yaml`:

```yaml
mqtt:
  host: <broker address>
  port: 8883
  username: <your id>
  password: <password>
  ca_cert_path: <CA certificate path, optional>
  base_topic: bip/mqtt-lab
  qos: 2
  keepalive: 60

serial:
  port: COM5
  baud_rate: 115200
  timeout: 1.0

telemetry:
  enabled: true
  publish_rate_hz: 0.5
```

