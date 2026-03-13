
# MQTT Crane Interface

## Commands

### Hoist (Moves up and down)

- **Request topic**: `{base-topic}/{crane-id}/req/{response-id}/hoist`
- **Payload**:
  ```json
  { "height": 150 }
  ```
  Height between [0 mm and 200 mm]
- **Response topic**: `{base-topic}/{crane-id}/res/{response-id}/hoist`
- **Response payload**:
  ```json
  { "height": 151.3, "result": "success" }
  ```
  `height` is the achieved final height `result` is `"success"` or `"timeout"` if the height could not be reached.

### Move (Moves left and right)

- **Request topic**: `{base-topic}/{crane-id}/req/{response-id}/simplemove`
- **Payload**:
  ```json
  { "position": 200 }
  ```
  Position between 0 mm and 445 mm
- **Response topic**: `{base-topic}/{crane-id}/res/{response-id}/simplemove`
- **Response payload**:
  ```json
  { "position": 199.8, "result": "success" }
  ```
  `position` is the achieved final position `result` is `"success"` or `"timeout"` if the position could not be reached.

