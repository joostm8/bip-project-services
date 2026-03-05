Start-Process  -FilePath "python" -ArgumentList "examples/conveyor_belt_g2mqtt/run_g_to_mqtt.py"
Start-Process  -FilePath "python" -ArgumentList "examples/crane_optimal_control/run_mqtt_database_writer.py"
Start-Process  -FilePath "python" -ArgumentList "examples/crane_optimal_control/run_mqtt_gantry_controller.py"
Start-Process  -FilePath "python" -ArgumentList "examples/crane_optimal_control/run_mqtt_trajectory_generator.py"
Start-Process  -FilePath "python" -ArgumentList "examples/ship_simulator/run_ship_simulation.py"

Write-Host "All scripts have been started."
