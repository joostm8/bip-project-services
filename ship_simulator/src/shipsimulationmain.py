import asyncio
import logging
from typing import Dict, Any

from connectivity import ShipConnectivity
from shipstatus import StatusManager
from simcontrol import SimulationController
from shipsimulation import ShipSimulation
from container import Container


class ShipSimulationSystem:
    def __init__(self, broker: str, port: int, ship_id: str, username: str = None, password: str= None):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.connectivity = ShipConnectivity(
            broker=broker,
            port=port,
            client_id=ship_id,
            username=username,
            password=password
        )
        
        self.ship_simulation = ShipSimulation(
            width_slots=5,
            height_slots=5,
        )
        
        self.controller = SimulationController(
            connectivity=self.connectivity,
            ship_simulation=self.ship_simulation,
        )
        
        self.status_manager = StatusManager(
            connectivity=self.connectivity
        )
        
        # Register message handlers
        self.setup_message_handlers()

    def setup_message_handlers(self):
        """Setup all MQTT message handlers"""
        # Container placement requests
        self.connectivity.register_message_handler(
            f"control/ship/{self.connectivity.client_id}/containers/incoming",
            self.handle_container_request
        )
        self.connectivity.register_message_handler(
            f"control/ship/{self.connectivity.client_id}/containers/outgoing",
            self.handle_container_remove
        )

    async def handle_container_remove(self, payload: Dict[str, Any]):
        """Handle a container remove"""
        try:
            self.logger.info("Received a container remove: {coordinates}")
            await self.status_manager.set_loading_status()

            coordinates = payload['position']

            success, message, heel_angle, container = self.ship_simulation.process_container_remove(
                x_slot=coordinates["x"],
                y_slot=coordinates["y"]
            )

            # Get new telemetry
            telemetry = self.ship_simulation.get_telemetry()

            # Update status based on new telemetry
            await self.status_manager.update_status_from_telemetry(telemetry)

            self.logger.info(f"Container placement {'successful' if success else 'failed'}: {message}")

            # Publish updated telemetry
            await self.connectivity.publish_telemetry(telemetry)

            return success
        except Exception as e:
            self.logger.error(f"Error processing container removal: {str(e)}")
            await self.status_manager.set_error_status(str(e))
            return False

    async def handle_container_request(self, payload: Dict[str, Any]):
        """Handle incoming container placement requests"""
        try:
            self.logger.info(f"Received container request: {payload}")

            # Update status to loading
            await self.status_manager.set_loading_status()

            # Create container object from payload
            container_data = payload['container']
            container = Container(
                weight=container_data['weight'],
                container_id=container_data['container_id']
            )

            # Get position
            position = payload['position']
            x_slot = position['x']
            y_slot = position['y']

            # Add container to ship
            success, message, heel_angle = self.ship_simulation.process_container_add(container, x_slot, y_slot)

            # Get new telemetry
            telemetry = self.ship_simulation.get_telemetry()

            # Update status based on new telemetry
            await self.status_manager.update_status_from_telemetry(telemetry)

            self.logger.info(f"Container placement {'successful' if success else 'failed'}: {message}")

            # Publish updated telemetry
            await self.connectivity.publish_telemetry(telemetry)

            return success

        except Exception as e:
            self.logger.error(f"Error processing container request: {str(e)}")
            await self.status_manager.set_error_status(str(e))
            return False

    async def start(self):
        """Start the simulation system"""
        try:
            # Connect to MQTT broker
            self.logger.info("Starting MQTT connection...")
            await self.connectivity.start()
            
            # Publish initial status and telemetry
            telemetry = self.ship_simulation.get_telemetry()
            await self.connectivity.publish_telemetry(telemetry)
            await self.status_manager.update_status_from_telemetry(telemetry)
            
            self.logger.info("Ship simulation system started successfully")
            
            # Keep the system running
            while True:
                await asyncio.sleep(3600)  # Just keep the system alive
                
        except Exception as e:
            self.logger.error(f"Error in simulation system: {str(e)}")
            raise

    async def stop(self):
        """Stop the simulation system"""
        self.logger.info("Stopping simulation system...")
        await self.connectivity.stop()

async def main():
    # Configuration
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    SHIP_ID = "1"
    UNAME = "shipsim"
    PWD = "shipsim"
    
    # Create and start simulation system
    simulation = ShipSimulationSystem(
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        ship_id=SHIP_ID,
        username=UNAME,
        password=PWD
    )
    
    try:
        await simulation.start()
    except KeyboardInterrupt:
        await simulation.stop()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        await simulation.stop()
        raise

if __name__ == "__main__":
    asyncio.run(main())
