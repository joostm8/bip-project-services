# bip-project-services
Repo containing all mqtt services needed for the bip project

## Setup

The following steps should help you getting an up and running project.

1. clone this directory to your computer
     git clone https://github.com/joostm8/bip-project-services.git
2. open the cloned folder in your editor of choice, e.g. Visual Studio Code or PyCharm
3. If you have not yet installed it, install [python](https://www.python.org/)
4. Create a new virtual environment in python to install the various python packages. For VSCode that is:
   - Open the command palette with Ctrl+Shift+P
   - Select the option `Python: Select Interpreter`
   - Select the option `Create Virtual Environment`
   - Select the option `Venv`
   - Select the Python version you'd like
   - A new virtual environment is now created in your workspace.
5. Install all the packages needed for the various services. For VSCode that is:
   - Open a new terminal (Terminal > Open a new terminal or press Ctrl + Shift + `)
   - execute `pip install paho-mqtt pyserial numpy PyYAML psycopg[binary] rockit-meco pytrinamic opencv-python`
6. Set up a tunnel to the VM running the database, dashboard and mqtt broker. [Instructions can be found here](https://github.com/joostm8/bip-project-services/blob/main/README.md#connecting-to-vm-on-server) **OR** run your database, Grafana and MQTT broker locally by setting up the docker containers you download from Blackboard `Intensive Week > Case Study and Labs > docker-containers-student-backup.zip`, the readme is in the .zip archive.
7. To make your life easier, if you're running visual studio code, we have included a launch file and a launch task in `.vscode/launch.json` and `.vscode/tasks.json`.
   - The launch file allows you to run any python file in a new terminal. Just open the file, then press `Ctrl + F5` to run the launch configuration. Helpful when you want to spawn a new process.
   - The task file contains a task that spawns all the mqtt services at once, side-by-side in your terminal. To run it, you
     - Press `Ctrl + Shift + P` to open the command palette
     - Select `Tasks: Run Task`
     - Select the task `Run All`
8.  You're all set, refer to the readmes of the services for further details, and specifically on how to configure your group ID in the files!
   Also have a look inside the bip-teacher-solution-main folder at the [minimal_example.py](./bip-teacher-solution-main/minimal_example.py).

## Services Tutorials 
- [Conveyor Belt](./conveyor_belt_G2MQTT/README.md)
- [Ship Simulator](./ship_simulator/README.md)
- [Crane System](./crane_optimal_control/README.md)
- [Marker Identification](./aruco_identification/README.md)
- [Teacher Solution](./bip-teacher-solution-main/README.md)

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

### aruco marker identification
No dependencies

### Teacher solution
- `mqtt_gantry_controller.py`
- `mqtt_trajectory_generator.py`
- `mqtt_database_writer.py`
- `mqtt_aruco_detector.py`
- `GtoMQTT.py`

## Grafana dashboard

The dashboard is available on [localhost:3000](http://localhost:3000)

The username is `admin` and the password is `default`.

You'll find the visualization in `hamburger menu top left > dashboards > general > harbour-viz`

## Connecting to VM on server

**Authenticate with your student username and password in the [VPN](https://www.uantwerpen.be/en/library/search-help/remote-access/)**

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
