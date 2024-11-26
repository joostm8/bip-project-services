import paho.mqtt.client as mqtt
import json
import logging
from typing import Callable, Dict, Any
import asyncio

class ShipConnectivity:
    def __init__(self, broker: str, port: int, client_id: str, username: str = None, password: str = None):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
        if username is not None and password is not None:
            self.client.username_pw_set(username=username, password=password)
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.loop = asyncio.get_event_loop()
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Message handlers dictionary
        self.message_handlers: Dict[str, Callable] = {}
        
        # Setup default topics
        self.topics = {
            f"control/ship/{client_id}/containers/incoming": "Container placement requests",
            f"control/ship/{client_id}/containers/outgoing": "Container removal requests",
            f"telemetry/ship/{client_id}": "Ship telemetry data",
            f"status/ship/{client_id}": "Ship status updates",
            f"control/ship/{client_id}/commands":"Sim commands"
        }

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to broker {self.broker}:{self.port}")
            
            # Subscribe to all relevant topics
            for topic in self.topics:
                self.client.subscribe(topic)
                self.logger.info(f"Subscribed to {topic}")
        else:
            self.logger.error(f"Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.connected = False
        self.logger.warning("Disconnected from broker")
        if rc != 0:
            self.logger.error(f"Unexpected disconnection. Attempting reconnection...")
            self.start()

    def _on_message(self, client, userdata, message):
        try:
            topic = message.topic
            self.logger.info(f"Received message on topic {topic}")
            payload = json.loads(message.payload.decode())
            
            if topic in self.message_handlers:
                asyncio.run_coroutine_threadsafe(
                    self.message_handlers[topic](payload),
                    self.loop
                )
            else:
                self.logger.warning(f"No handler for topic: {topic}")
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON payload received on topic {message.topic}")
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    async def start(self):
        """Start the MQTT client with automatic reconnection"""
        while not self.connected:
            try:
                self.client.connect_async(self.broker, self.port)
                self.client.loop_start()
                
                # Wait for connection or timeout
                for _ in range(10):  # 5 seconds timeout
                    if self.connected:
                        break
                    await asyncio.sleep(0.5)
                    
                if not self.connected:
                    raise ConnectionError("Connection timeout")
                    
            except Exception as e:
                self.logger.error(f"Connection failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry

    def stop(self):
        """Stop the MQTT client"""
        self.client.loop_stop()
        self.client.disconnect()

    async def publish_telemetry(self, telemetry_data: Dict[str, Any]):
        """Publish telemetry data"""
        if not self.connected:
            self.logger.warning("Cannot publish telemetry - not connected")
            return False
            
        try:
            topic = f"telemetry/ship/{self.client_id}"
            payload = json.dumps(telemetry_data)
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"Failed to publish telemetry: {result.rc}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing telemetry: {str(e)}")
            return False

    async def publish_status(self, status: str):
        """Publish ship status updates"""
        if self.connected:
            topic = f"status/ship/{self.client_id}"
            payload = json.dumps({"status": status, "timestamp": asyncio.get_event_loop().time()})
            self.client.publish(topic, payload, qos=1)

    def register_message_handler(self, topic: str, handler: Callable):
        """Register a handler for a specific topic"""
        self.message_handlers[topic] = handler
        if self.connected:
            self.client.subscribe(topic)
