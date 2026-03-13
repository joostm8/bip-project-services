# ShipSimulation Class

This class models container loading and calculates ship stability.
It does not handle MQTT directly.

Import it with 

```python
from ship_simulator.container import Container
from ship_simulator.shipsimulation import ShipSimulation
```

## Initialization

```python
sim = ShipSimulation(width_slots=5, height_slots=5)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `width_slots` | — | Number of container columns (horizontal) |
| `height_slots` | — | Number of container rows (vertical) |
| `container_width` | 2.4 m | Width of one container slot. Keep at default |
| `container_height` | 2.6 m | Height of one container slot. Keep at default |

## Container

Containers are created with:

```python
container = Container(weight=20000, container_id="CONT001")
```

`weight` is in kilograms.

## Grid Layout

The ship grid uses `(x, y)` coordinates:

- **x** — columns (horizontal): Facing the ship, `x=0` is the left, `x=width_slots-1` is right.
- **y** — rows (vertical): `y=0` is the bottom level, `y=height_slots-1` is the top row.

Containers can only be placed on top of another container or on the bottom row (`y=0`).
Only the topmost container in a column can be removed.

## Methods

### Adding containers

#### `process_container_add(container, x_slot, y_slot, max_heel_angle=5.0)`

Adds a container to the grid and returns the new heel angle.

```python
success, message, heel_angle = sim.process_container_add(container, x_slot=2, y_slot=0)
```

Returns `(bool, str, float)`.
If placement is invalid, `success` is `False` and `message` explains why.

### Removing containers

#### `process_container_remove(x_slot, y_slot)`

Removes the container at the given position (must be the topmost in its column).

```python
success, message, heel_angle, removed_container = sim.process_container_remove(x_slot=2, y_slot=0)
```

Returns `(bool, str, float, Container | None)`.

### Placement checks

#### `is_valid_placement(x_slot, y_slot)`

Returns `(bool, str)`.
The second value is a message explaining whether placement is valid.

#### `find_next_valid_position(x_slot)`

Returns the lowest free `y_slot` in the given column, or `None` if the column is full.

#### `is_highest_on_column(y, x)`

Returns `True` if the slot `(x, y)` holds the topmost container in its column (i.e., it can be removed).

### Stability and telemetry

#### `get_telemetry()`

Returns a dict with the current ship stability metrics. Use this to get an overview of the ship state.

```python
telemetry = sim.get_telemetry()
# Keys: KB, BM, KG, GM, GZ, righting_moment,
#       effective_beam, waterplane_area, heel_angle, draught
```

| Key | Unit | Description |
|-----|------|-------------|
| `GM` | m | Metacentric height — main stability indicator. Positive = stable. |
| `heel_angle` | ° | Current equilibrium heel angle |
| `draught` | m | Current draught (depth below waterline) |
| `KB` | m | Height of centre of buoyancy above keel |
| `BM` | m | Distance from centre of buoyancy to metacentre |
| `KG` | m | Height of centre of gravity above keel |
| `GZ` | m | Righting arm at current heel angle |

#### `calculate_equilibrium_heel()`

Iteratively finds the equilibrium heel angle where heeling and righting moments balance. More accurate than `calculate_heel_angle()`.

```python
heel_angle, stability = sim.calculate_equilibrium_heel()
```

Returns `(float, dict)`.

#### `calculate_stability_at_heel(heel_angle_deg)`

Returns the full stability dict `{KB, BM, KG, GM, GZ, righting_moment, ...}` for the given heel angle.

#### `calculate_draught()`

```python
draught, info = sim.calculate_draught()
```

`info` contains `draught`, `displacement_volume`, `design_draught`, `load_percentage`, `total_weight`.

#### `calculate_center_of_mass()`

Returns `(x, y)` of the combined centre of mass (hull + containers).

#### `get_total_weight()`

Returns total weight in kg (hull + all containers, scaled along the ship length).

### Debug output

#### `print_loading_info()`

Prints a summary of current loading: total weight, draught, load percentage.

#### `print_stability_analysis()`

Prints KB, BM, KG, GM, GZ, righting moment, and equilibrium heel angle.

---

## Fault injection

Use Fault injection on either the digital twin or the real ship to inject random faults in the container weight, which you can detect by comparing the real ship with the twin.

```python
sim.enable_fault_injection()   # activates hidden weight modification for specific positions
sim.disable_fault_injection()  # deactivates and clears injected data
```
