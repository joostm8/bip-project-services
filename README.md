# bip-project-services
Repo containing all mqtt services needed for the bip project


## Services Tutorials 
- [Conveyor Belt](./conveyor_belt_G2MQTT/README.md)
- [Ship Simulator](./ship_simulator/README.md)
- [Trajectory Generation](./crane_optimal_control/README.md)

## Services dependencies

### crane
- mqtt_gantry_controller.py - Depends on:
  - mqtt_trajectory_generator.py
  - mqtt_database_writer.py
  - TimescaleDB database

### conveyor system
No dependencies between

### ship simulation
No dependencies

## Connecting to VM on server

We have a VM set up that is running
- A timescaleDB database
  - user: postgres
  - password: postgres\
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
  - password: ay2024-2025-[<device-name>]
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

Just database and mqtt broker:

ssh -i ~/.ssh/netlab -L 3000:localhost:3000 -L 5432:localhost:5432 -L 1883:localhost:1883 [<yourstudentID>]@143.129.43.20

Don't close this terminal. All ports can now be accessed with localhost:portnumber.
