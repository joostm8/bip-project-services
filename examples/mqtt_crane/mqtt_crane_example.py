from mqtt_crane.mqtt_crane_controller import MQTTCraneController


if __name__ == "__main__":
    wrapper = MQTTCraneController("./crane_optimal_control/gantry_system/crane-properties.yaml", mock = True)
    wrapper.start()