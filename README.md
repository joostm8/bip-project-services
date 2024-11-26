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

### conveyor system
No dependencies between

### ship simulation
No dependencies
