from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from conveyor_belt_g2mqtt import g_to_mqtt


def run() -> None:
    client = g_to_mqtt.mqtt.Client()
    g_to_mqtt.client = client

    client.on_connect = g_to_mqtt.on_connect
    client.on_message = g_to_mqtt.on_message
    client.connect(g_to_mqtt.MQTT_BROKER, g_to_mqtt.MQTT_PORT, keepalive=60)

    client.loop_start()
    serial_thread = threading.Thread(target=g_to_mqtt.serial_to_mqtt, daemon=True)
    serial_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if g_to_mqtt.ser:
            g_to_mqtt.ser.close()
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
