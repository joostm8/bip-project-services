from pathlib import Path
import sys
import time

from conveyor_belt_g2mqtt import g_to_mqtt


def run() -> None:
    service = g_to_mqtt.ConveyorMQTTService("../config.yaml")
    service.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        service.stop()


if __name__ == "__main__":
    run()
