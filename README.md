# bip-project-services
Repo containing all mqtt services needed for the bip project


## Services Tutorials 
- [Conveyor Belt](./conveyor_belt_G2MQTT/README.md)
- [Ship Simulator](./ship_simulator/README.md)
- [Crane System](./crane_optimal_control/README.md)

## Services dependencies

### crane
- mqtt_gantry_controller.py - Depends on:
  - mqtt_trajectory_generator.py
  - mqtt_database_writer.py
  - TimescaleDB database
 
The dependency on the database can be disabled by using method `mqttMoveWithoutLog` instead of `mqttMoveWithLog`. You could add an MQTT topic for this if needed,
or make the change yourself in `mqtt_trajectory_generator.py`. TODO Joost: implement this.


### conveyor system
No dependencies between

### ship simulation
No dependencies

## Connecting to VM on server

We have a VM set up that is running
- A timescaleDB database
  - user: postgres
  - password: postgres
  - database: gantrycrane
  - port: 5432
- MQTT broker
  - no authentication
  - port: 1883
- Grafana dashboard
  - user: admin
  - password: default
  - port: 3000 
- Eclipse Hono
  - tenant ID: bip-server
  - devices: crane-1, crane-2, crane-3, conveyor-1, conveyor-2, conveyor-3
  - password: ay2024-2025-devicename
  - MQTT port: 8883
  - AMQP Southbound port: 5671
  - HTTP port: 8443
  - device registry: 28443
  - AMQP Northbound port: 15671, 15672

Assuming the keyfile you generated is in `~/.ssh/netlab` (if you're on Windows it's likely in `C:\Users\[<yourusername>]\.ssh\netlab`), the command to set up and ssh tunnel is: 

All ports:

    ssh -i ~/.ssh/netlab -L 3000:localhost:3000 -L 5432:localhost:5432 -L 1883:localhost:1883 -L 5671:localhost:5671 -L 8443:localhost:8443 -L 8883:localhost:8883 -L 15671:localhost:15671 -L 15672:localhost:15672 -L 28443:localhost:28443 [<yourstudentID>]@143.129.43.20

Just Hono ports:

    ssh -i ~/.ssh/netlab -L 3000:localhost:3000 -L 5671:localhost:5671 -L 8443:localhost:8443 -L 8883:localhost:8883 -L 15671:localhost:15671 -L 15672:localhost:15672 -L 28443:localhost:28443 [<yourstudentID>]@143.129.43.20

Just database, grafana and mqtt broker:

    ssh -i ~/.ssh/netlab -L 3000:localhost:3000 -L 5432:localhost:5432 -L 1883:localhost:1883 [<yourstudentID>]@143.129.43.20

Don't close this terminal. All ports can now be accessed with localhost:portnumber.

## Database tables

**IMPORTANT** all groups have access to all database tables. Usually there is a `machine_id`, `id` or similar as one of the columns in the table.
When you make database writes, make sure to put that field to your own group number to not overwrite data of other groups. In the table description below, we have added a **this is your group identifier** for each of the tables.

For the `mqtt_database_writer.py`, this is handled for you if you set the `machine id` field in `crane-properties.yaml`. 

Preferably use a program such as DBeaver [https://dbeaver.io/] to view the database tables.

Below, the tables are described in alphabetical order.

### table - cargomanifest

Table containing the cargomanifest, that is, which container is expected to be at which position

|slot|pos_x|pos_y|state|container_id|ship_id|
|----|-----|-----|-----|------------|-------|

- slot: the slot id, a slot is a fillable space on the ship
- pos_x: the x position of the slot
- pos_y: the y position of the slot
- state: {empty, fillable, filled}, the state of the slot
- container_id: the id of the container that is supposed to fill this slot. Right now a simple 1 to 1 mapping of slot to container id is used.
- ship_id: the id of the ship to which this slot belongs to. **this is your groupd identifier**

### table - container

|container_id|weight|
|------------|------|

- container_id: the container id
- weight: the weight of this container

This table is common for all groups, therefore there is no group identifier

### table - machine

|machine_id|name|
|----------|----|

- machine_id: the id of the crane/machine. **this is your groupd identifier**
- name: a description

### table - measurement

|ts|machine_id|run_id|quantity|value|
|--|----------|------|--------|-----|

- ts: timestamp
- machine_id: id of the machine to which this measurement belongs. **this is your groupd identifier**
- run_id: id of the run (that is, a single trajectory)
- quantity: the quantity of the value
- value: value of the measurement

### table - quantity

|name|symbol|unit|
|----|------|----|

- name: name of the quantity {position, velocity, acceleration, angular position, angular velocity, angular acceleration, force}
- symbol: symbol of that quantity
- unit: unit of the quantity

This table is common for all groups, therefore there is no group identifier

### table - quay

|slot|pos_x|pos_y|state|container_id|machine_id|
|----|-----|-----|-----|------------|----------|

- slot: the slot id, a slot is a fillable space on the quay
- pos_x: the x position of the slot
- pos_y: the y position of the slot
- state: {empty, fillable, filled}, the state of the slot
- container_id: the id of the container that is currently occupying this spot. NULL when not occupied
- ship_id: the id of the ship to which this slot belongs to. **this is your groupd identifier**

### table - quay

|run_id|machine_id|starttime|
|------|----------|---------|

This table is used to store the starttime of a run.

- run_id: the id of the run
- machine_id: the id of the machine executing the run. **this is your groupd identifier**
- starttime: the starttime of the run


### table - ship

|id|roll|draft|
|--|----|-----|

- id: the id of the ship. **this is your groupd identifier**
- roll: the roll of the ship
- draft: the draft of the ship

### table - trajectory

This table is the equivalent of table measurement, but then to store the generated trajectories.

|ts|machine_id|run_id|quantity|value|
|--|----------|------|--------|-----|

- ts: timestamp
- machine_id: id of the machine to which this measurement belongs. **this is your groupd identifier**
- run_id: id of the run (that is, a single trajectory)
- quantity: the quantity of the value
- value: value of the measurement
