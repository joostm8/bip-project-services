from pathlib import Path

from mqtt_crane.mqtt_crane_controller import MQTTCraneController


if __name__ == "__main__":
    wrapper = MQTTCraneController("../config.yaml", mock=False)
    wrapper.start()