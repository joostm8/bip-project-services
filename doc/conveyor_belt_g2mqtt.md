# Conveyor Belt G2MQTT Interface

## Commands

### G1 – Move continuously

- **Request topic**: `{base_topic}/{crane-id}/req/{response-id}/G1`
- **Payload**:
```json
{ "dir": "F" }
```

`dir`: `"F"` (forward) or `"B"` (backward). Runs until stopped.

- **Response topic**: `{base_topic}/{crane-id}/res/{response-id}/G1`
- **Response payload**: None
### G2 – Move for a fixed duration

- **Request topic**: `{base_topic}/{crane-id}/req/{response-id}/G2`
- **Payload**:
```json
{ "dir": "F", "duration": 500 }
```
`dir`: `"F"` (forward) or `"B"` (backward). `duration`: time in milliseconds, range `0` to `10000`.

- **Response topic**: `{base_topic}/{crane-id}/res/{response-id}/G1`
- **Response payload**: None

### G3 – Move until sensor

- **Request topic**: `{base_topic}/{crane-id}/req/{response-id}/G3`
- **Payload**:
```json
{ "dir": "F" }
```

`dir`: `"F"` (forward) or `"B"` (backward). Moves the conveyor until the start or end sensor is triggered.

- **Response topic**: `{base_topic}/{crane-id}/res/{response-id}/G1`
- **Response payload**: None

### G4 – Query sensor state
- **Request topic**: `{base_topic}/{crane-id}/req/{response-id}/G4`
- **Payload**: None
- **Response topic**: `{base_topic}/{crane-id}/res/{response-id}/G4`
- **Response payload**: 
```json
{ "START_SENSOR": `, "END_SENSOR": 0, "PULSE_COUNT": 42 }
```

### G5 – Stop

- **Request topic**: `{base_topic}/{crane-id}/req/{response-id}/G5`
- **Payload**: None
- **Response topic**: `{base_topic}/{crane-id}/res/{response-id}/G5`
- **Response payload**: None

### G6 – Toggle Electromagnet

- **Request topic**: `{base_topic}/{crane-id}/req/{response-id}/G6`
- **Payload**:
```json
{ "on/off": 1 }
```

`0` = off, `1` = on.

- **Response topic**: `{base_topic}/{crane-id}/res/{response-id}/G6`
- **Response payload**: None

## Swing Encoder Telemetry

Published automatically to `{base_topic}/{id}/telemetry`:

```json
{ "A": 2.75, "V": 1.33 }
```

`A` = angle, `V` = angular velocity.
