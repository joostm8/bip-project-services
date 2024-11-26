Start-Process  -FilePath "python" -ArgumentList "conveyor_belt_G2MQTT/GtoMQTT.py"
Start-Process  -FilePath "python" -ArgumentList "crane_optimal_control/mqtt_database_writer"
Start-Process  -FilePath "python" -ArgumentList "crane_optimal_control/mqtt_gantry_controller.py"
Start-Process  -FilePath "python" -ArgumentList "crane_optimal_control/mqtt_trajectory_generator.py"
Start-Process  -FilePath "python" -ArgumentList "ship_simulator/src/shipsimulationmain.py"

Write-Host "All scripts have been started."
