# bip-project-services

This repo contains all the services for the bip project.

## Documentation for students

### Installation

You have to install this repository as a package to use the packages in your code.

First clone the repository with the command

`git clone https://github.com/joostm8/bip-project-services.git`

Navigate into the folder

`cd bip-project-services`

Checkout the `flat-to-src-layout-refactor` branch

`git checkout flat-to-src-layout-refactor`

Install the repository as a package

`pip install -e .`

Test the installation by opening for example the teacher notebook and testing the imports.

### MQTT interfaces

In the [doc](./doc/) folder you will find a description of the available MQTT interfaces.

You can:
- [Scan ArUco markers to identify containers](./doc/aruco_identification.md)
- [Control the conveyor belt's movement](./doc/conveyor_belt_g2mqtt.md)
- [Control the crane's movement](./doc/mqtt_crane.md)
- [Control the crane's electromagnet](./doc/conveyor_belt_g2mqtt.md)

To setup your own MQTT connection to the broker, reuse the credentials given to you in the MQTT-lab
* Credentials: reuse the credentials given to you in the MQTT-lab
* The `{base-topic}` is `bip/mqtt-lab`
* The `{crane-id}` is `crane-pi-1` or `crane-pi-2`
* The `{response-id}` you generate (e.g. a `uuid`) to be able to map requests to responses

### Ship Simulation

You'll also find [a description of the ship simulator's functions](./doc/ship_simulator.md)

### Teacher solution

Lastly, you'll find the [teacher solution](./examples/bip_teacher_solution_main/harbour_terminal_solution.ipynb) as demonstrated at the start of the lecture.

## Documentation for lab assistants

The examples folder contains the three services you need to run up to make the entire system available over MQTT.

- [The crane](./examples/mqtt_crane/mqtt_crane_example.py)
- [The conveyor](./examples/conveyor_belt_g2mqtt/run_g_to_mqtt.py)
- [The ArUco scanner](./examples/aruco_identification/run_mqtt_aruco_detector.py)

### Setting up the environment

I'm assuming you are using VS Code with Python extensions enabled.

1. Install Python 3.13 or up
2. Create a new or select an existing virtual environment
    1. Ctrl+Shift+P to open the command pallette
    2. Python: Select Interpreter
    3. Create Virtual Environment or select an existing one
    4. Windows: make sure running scripts is enabled in Powershell. Open a Powershell as administrator and run `set-executionpolicy remotesigned`
3. Open a new terminal in the repository root, check that the virtual environment is correctly activated
4. Download or clone the repository https://github.com/Cosys-Lab/lab-scale-gantry-crane
5. Install that repository as editable package with `pip install -e <path-to-lab-scale-gantry-crane>` (needed for the mqtt crane)
6. Install this repository as editable package with `pip install -e .`

### Setting up the config

In the [config.yaml](./examples/config.yaml), you need to specify the ports of the Arduino, the motor drivers and the video device.

#### Windows
Inspect device manager for the serial ports and run the [list_cameras.py](./examples/aruco_identification/list_cameras.py) script for the video device.


#### Linux

Run `ls /dev | grep tty` for serial device paths and `v4l2-ctl --list-devices` for the video device path. I've also added the[tty_path_to_device.bash](./examples/tty_path_to_device.bash) which maps the device path to a name, to differentiate motor drivers from the Arduino.

### Running the three services

A VS Code task is provided to make launching these easy.

1. Ctrl+Shift+P
2. Tasks: Run Task
3. `Run Aruco + Conveyor + MQTT Crane`

Three terminals should spawn side-by-side and start the three services.

The terminal running `mqtt_crane.py` is going to ask for zeroing the hoist, which you must confirm with enter. If no movement occurs on the crane, double check that the crane's power supply is on.

