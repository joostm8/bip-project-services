import asyncio
import json
from paho.mqtt.client import Client, MQTTv5
from datetime import datetime


class ShipTestClient:
    def __init__(self, ship_id="ship001"):
        self.client = Client(protocol=MQTTv5)
        self.ship_id = ship_id
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.latest_telemetry = None

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"Connected with result code {rc}")
        self.client.subscribe(f"telemetry/ship/{self.ship_id}")
        self.client.subscribe(f"status/ship/{self.ship_id}")

    def _on_message(self, client, userdata, msg):
        if "telemetry" in msg.topic:
            self.latest_telemetry = json.loads(msg.payload)
            self._print_telemetry()
        else:
            print(f"\nReceived {msg.topic}:")
            print(json.loads(msg.payload))

    def _print_telemetry(self):
        if self.latest_telemetry:
            print("\n=== Ship Telemetry ===")
            print(f"Heel Angle: {self.latest_telemetry.get('heel_angle', 0):.2f}°")
            print(f"GM: {self.latest_telemetry.get('GM', 0):.2f}m")
            print(f"GZ: {self.latest_telemetry.get('GZ', 0):.2f}m")
            print(f"Draught: {self.latest_telemetry.get('draught', 0):.2f}m")
            print("==================")

    async def connect(self):
        self.client.username_pw_set("shipsim", "shipsim")
        self.client.connect("localhost", 1883)
        self.client.loop_start()
        await asyncio.sleep(1)

    async def request_telemetry(self):
        # Request telemetry by sending a dump state command
        payload = {
            "command": "DUMP_STATE"
        }
        self.client.publish(
            f"control/ship/{self.ship_id}/commands",
            json.dumps(payload)
        )
        await asyncio.sleep(1)

    async def remove_container(self, x_pos, y_pos):
        payload = {
            "position": {
                "x": x_pos,
                "y": y_pos
            }
        }
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] removing container")
        print(f"Position: ({x_pos}, {y_pos})")

        self.client.publish(
            f"control/ship/{self.ship_id}/containers/outgoing",
            json.dumps(payload)
        )
        await asyncio.sleep(1)
        await self.request_telemetry()
        await asyncio.sleep(1)

    async def add_container(self, weight, container_id, x_pos, y_pos):
        payload = {
            "container": {
                "weight": weight,
                "container_id": container_id
            },
            "position": {
                "x": x_pos,
                "y": y_pos
            }
        }
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Adding container {container_id}")
        print(f"Weight: {weight / 1000:.1f} tons, Position: ({x_pos}, {y_pos})")

        self.client.publish(
            f"control/ship/{self.ship_id}/containers/incoming",
            json.dumps(payload)
        )
        await asyncio.sleep(1)
        await self.request_telemetry()
        await asyncio.sleep(1)

    async def send_reset_command(self):
        payload = {
            "command": "INITIALIZE"
        }
        self.client.publish(
            f"control/ship/{self.ship_id}/commands",
            json.dumps(payload)
        )
        await asyncio.sleep(1)
        await self.request_telemetry()

    async def send_FIE_command(self):
        payload = {
            "command": "ENABLE_FAULT_INJECTION"
        }
        self.client.publish(
            f"control/ship/{self.ship_id}/commands",
            json.dumps(payload)
        )
        await asyncio.sleep(1)
        await self.request_telemetry()


async def main():
    client = ShipTestClient()
    await client.connect()
    await client.send_FIE_command()

    try:
        # First phase: Load left side (column 0)
        print("\n=== Phase 1: Loading left side ===")
        containers_left = [
            (20000, "LEFT_1", 0, 0),  # Heavy base container
            (15000, "LEFT_2", 0, 1),
            (10000, "LEFT_3", 0, 2),
            (8000, "LEFT_4", 0, 3),
            (5000, "LEFT_5", 0, 4)
        ]

        for weight, cid, x, y in containers_left:
            await client.add_container(weight, cid, x, y)

        # Second phase: Balance with right side (column 4)
        print("\n=== Phase 2: Balancing right side ===")
        containers_right = [
            (20000, "RIGHT_1", 4, 0),  # Matching heavy base container
            (15000, "RIGHT_2", 4, 1),
            (10000, "RIGHT_3", 4, 2),
            (8000, "RIGHT_4", 4, 3),
            (5000, "RIGHT_5", 4, 4)
        ]

        for weight, cid, x, y in containers_right:
            await client.add_container(weight, cid, x, y)

        # Third phase: Fill middle columns
        print("\n=== Phase 3: Filling middle columns ===")
        containers_middle = [
            # Column 1
            (12000, "MID1_1", 1, 0),
            (10000, "MID1_2", 1, 1),
            (8000, "MID1_3", 1, 2),
            # Column 2 (center)
            (12000, "MID2_1", 2, 0),
            (10000, "MID2_2", 2, 1),
            (8000, "MID2_3", 2, 2),
            # Column 3
            (12000, "MID3_1", 3, 0),
            (10000, "MID3_2", 3, 1),
            (8000, "MID3_3", 3, 2),
            # Additional middle containers
            (5000, "MID1_4", 1, 3),
            (5000, "MID2_4", 2, 3),
            (5000, "MID3_4", 3, 3),
            (3000, "MID1_5", 1, 4),
            (3000, "MID2_5", 2, 4),
            (3000, "MID3_5", 3, 4)
        ]

        for weight, cid, x, y in containers_middle:
            await client.add_container(weight, cid, x, y)

        await client.remove_container(0,4)
        await client.remove_container(0, 3)
        await client.add_container(5000, "LEFT_5", 0, 3)
        await client.add_container(8000, "LEFT_4", 0, 4)

        print("\n=== Final Phase: Resetting Ship ===")
        await client.send_reset_command()
        print("Test completed. Press Ctrl+C to exit.")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down")


if __name__ == "__main__":
    asyncio.run(main())