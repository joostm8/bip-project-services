# ArUco Identification MQTT Interface

## Commands

### Request detected ArUco IDs

- **Request topic**: `{base-topic}/{crane-id}/req/{response-id}/aruco-id`
- **Payload**: none required
- **Response topic**: `{base-topic}/{crane-id}/res/{response-id}/aruco-id`
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
