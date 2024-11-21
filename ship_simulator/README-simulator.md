# Ship Loading Simulation - User Manual


### Component Description
- **ShipConnectivity**: Handles all MQTT communication
- **ShipSimulationSystem**: Main controller integrating all components
- **ShipSimulation**: Core simulation logic and stability calculations
- **StatusManager**: Monitors ship operational and safety status
- **SimulationController**: Handles simulation commands
- **Container**: Data model for container information

## Getting Started

### System Requirements
- Python 3.8 or higher
- MQTT Broker (e.g., Mosquitto)
- Required Python packages:
  - paho-mqtt
  - numpy
  - logging

### Starting the Simulation
```python
simulation = ShipSimulationSystem(
    broker="localhost",
    port=1883,
    ship_id="ship001",
    username="shipsim",
    password="shipsim"
)
await simulation.start()
```

## MQTT Communication

### Topic Structure
The simulation uses the following MQTT topics (replace `{ship_id}` with your ship identifier):

| Topic | Purpose |
|-------|---------|
| `control/ship/{ship_id}/containers/incoming` | Container placement requests |
| `control/ship/{ship_id}/containers/outgoing` | Container removal requests |
| `telemetry/ship/{ship_id}` | Ship telemetry data |
| `status/ship/{ship_id}` | Ship status updates |
| `control/ship/{ship_id}/commands` | Simulation commands |

### Message Formats

#### Adding a Container
```json
{
    "container": {
        "weight": 20000,
        "container_id": "CONT001"
    },
    "position": {
        "x": 2,
        "y": 0
    }
}
```

#### Removing a Container
```json
{
    "position": {
        "x": 2,
        "y": 0
    }
}
```

#### Simulation Commands
```json
{
    "command": "INITIALIZE",
    "params": {
        "width_slots": 5,
        "height_slots": 5
    }
}
```

## Ship Parameters

### Physical Dimensions
- Hull width: 30 meters
- Hull length: 180 meters
- Design draft: 12 meters
- Hull weight: 8,000,000 kg

### Container Grid
- Default configuration: 5x5 grid
- Container dimensions: 2.4m width × 2.6m height × 6.1m length
- Valid placement requires:
  - Position within grid bounds
  - Empty position
  - Support below (except bottom level)


### Status Types

#### Operational Status
- READY: Normal operations
- LOADING: Processing container operations
- FULL: Maximum capacity reached
- MAINTENANCE: System under maintenance
- ERROR: System error or critical condition

#### Safety Status
- STABLE: Normal conditions
- WARNING_HEEL: High heel angle detected
- WARNING_DRAFT: High draft level
- WARNING_STABILITY: Low stability margin
- CRITICAL: Critical safety condition

## Container Grid System

### Grid Layout
The ship's container storage is organized in a grid system (default 5x5) where:
- x-coordinate: represents position across ship's width (beam)
- y-coordinate: represents vertical position (height)
- (0,0) is at the bottom-left of the grid


### Coordinate System
- **X-Coordinates (Beam Position)**
  - Range: 0 to 4 (in default 5x5 grid)
  - x=0: Port side (left)
  - x=4: Starboard side (right)
  - Center at x=2
  - Each slot is 2.4m wide

- **Y-Coordinates (Height)**
  - Range: 0 to 4 (in default 5x5 grid)
  - y=0: Bottom level
  - y=4: Top level
  - Each slot is 2.6m high

### Placement Rules
1. **Valid Position Requirements**
   - x must be between 0 and (width_slots - 1)
   - y must be between 0 and (height_slots - 1)
   - Position must be empty
   - Must have support below (except y=0)

2. **Example Placement Message**
   ```json
   {
       "container": {
           "weight": 20000,
           "container_id": "CONT001"
       },
       "position": {
           "x": 2,  // Center position
           "y": 0   // Bottom level
       }
   }
   ```

### Impact on Stability
- **X-Position Effect**
  - Containers placed away from center (x=2) create heeling moments
  - Symmetrical loading across x-axis maintains stability
  - Greater x-distance from center creates larger heeling moments

- **Y-Position Effect**
  - Higher y-positions raise the ship's center of gravity (KG)
  - Increased KG reduces stability (smaller GM)
  - Top positions (higher y) have greater impact on stability

### Loading Best Practices
1. **Horizontal Loading**
   - Balance containers across x-positions
   - Start from center (x=2) when possible
   - Keep weight differences minimal between port and starboard

2. **Vertical Loading**
   - Fill lower positions (small y) first
   - Avoid top positions for heavy containers
   - Ensure proper support below

3. **Example Loading Sequence**
   ```
   Recommended loading order:
   1. (2,0) - Center, bottom
   2. (1,0) and (3,0) - Adjacent bottom positions
   3. (0,0) and (4,0) - Outer bottom positions
   4. Repeat pattern for higher levels
   ```

### Grid Information in Telemetry
The grid state can be obtained using the DUMP_STATE command:
```json
{
    "command": "DUMP_STATE"
}
```

Response includes grid information:
```json
{
    "ship_state": {
        "container_grid": [
            // 2D array representing container placement
            // null indicates empty position
            [/* y=0 row */],
            [/* y=1 row */],
            // ...
        ]
    }
}
```


## Stability Parameters

### Understanding Ship Stability
Ship stability is determined by the interaction of various forces and moments acting on the vessel. The key parameters help assess the ship's ability to return to an upright position when tilted by external forces.

### Key Parameters Explained

#### KB (Height of Center of Buoyancy)
- The vertical distance from the keel to the center of buoyancy
- The center of buoyancy is the geometric center of the underwater part of the ship
- Changes with ship's draft and heel angle
- Higher KB generally indicates deeper immersion in water

#### KG (Height of Center of Gravity)
- The vertical distance from the keel to the ship's center of gravity
- Affected by:
  - Hull weight distribution
  - Container placement
  - Total cargo weight
- Lower KG generally means better stability

#### BM (Metacentric Radius)
- The distance from the center of buoyancy to the metacenter
- Depends on the ship's beam (width) and underwater hull shape
- Larger BM indicates better initial stability
- Calculated using the ship's waterplane moment of inertia

#### GM (Metacentric Height)
- The distance from the ship's center of gravity to the metacenter
- GM = KB + BM - KG
- Critical stability indicator:
  - Positive GM: Ship is stable
  - Negative GM: Ship is unstable
  - Larger GM: More stable but can lead to rapid rolling
  - Smaller GM: More comfortable but less stable
- Thresholds in simulation:
  - Critical minimum: 0.5m
  - Optimal value: 2.0m

#### Heel Angle
- The angle of inclination around the ship's longitudinal axis
- Affected by:
  - Asymmetric loading
  - Wind forces
  - Turning forces
- Warning thresholds in simulation:
  - Warning level: 3.0°
  - Critical level: 5.0°

#### Draft (Draught)
- The vertical distance between the waterline and the bottom of the hull
- Indicates the ship's submergence
- Critical for:
  - Port accessibility
  - Under-keel clearance
  - Loading capacity
- Monitored as percentage of design draft (12.0m):
  - Warning level: 85%
  - Critical level: 95%



## Available Commands

### Command List
- INITIALIZE: Reset ship to initial state
- DUMP_STATE: Request current simulation state
- EMERGENCY: Activate emergency mode
- CLEAR_EMERGENCY: Deactivate emergency mode
- ENABLE_FAULT_INJECTION: Enable fault injection mode
- DISABLE_FAULT_INJECTION: Disable fault injection mode

### Example Command Messages

Initialize Simulation:
```json
{
    "command": "INITIALIZE",
    "params": {
        "width_slots": 5,
        "height_slots": 5
    }
}
```

Enable Fault Injection:
```json
{
    "command": "ENABLE_FAULT_INJECTION"
}
```

## Telemetry Data

The simulation provides real-time telemetry including:
- Current heel angle
- GM value
- Draft
- Stability parameters (KB, BM, KG)
- Righting moment

Example telemetry message:
```json
{
    "heel_angle": 2.5,
    "GM": 1.8,
    "draught": 10.5,
    "KB": 5.2,
    "BM": 8.4,
    "KG": 11.8,
    "righting_moment": 25000
}
```
