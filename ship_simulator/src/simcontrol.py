from enum import Enum
from dataclasses import dataclass
import json
from typing import Optional, Dict, Any

from container import Container
from shipsimulation import ShipSimulation
import logging


class SimCommand(Enum):
    INITIALIZE = "INITIALIZE"  # Reset ship to initial state
    DUMP_STATE = "DUMP_STATE" # Request current simulation state
    EMERGENCY = "EMERGENCY"   # Emergency mode - reject all new containers
    CLEAR_EMERGENCY = "CLEAR_EMERGENCY"  # Clear emergency mode
    ENABLE_FAULT_INJECTION = "ENABLE_FAULT_INJECTION"
    DISABLE_FAULT_INJECTION = "DISABLE_FAULT_INJECTION"

@dataclass
class SimulationConfig:
    width_slots: int = 5
    height_slots: int = 5
    container_width: float = 2.4
    container_height: float = 2.6
    hull_width: float = 20.0
    hull_length: float = 140.0
    design_draft: float = 12.0
    hull_weight: float = 8_000_000

class SimulationController:
    def __init__(self, connectivity, ship_simulation):
        self.connectivity = connectivity
        self.simulation = ship_simulation
        self.emergency_mode = False
        self.config = SimulationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Register command handler
        self.connectivity.register_message_handler(
            f"control/ship/{connectivity.client_id}/commands",
            self.handle_command
        )

    async def handle_command(self, payload: Dict[str, Any]):
        try:
            command = SimCommand(payload["command"])
            params = payload.get("params", {})
            
            response = {
                "command": command.value,
                "status": "success",
                "message": None
            }

            if command == SimCommand.ENABLE_FAULT_INJECTION:
                self.simulation.enable_fault_injection()
                response["message"] = "Fault injection enabled"

            elif command == SimCommand.DISABLE_FAULT_INJECTION:
                self.simulation.disable_fault_injection()
                response["message"] = "Fault injection disabled"

            if command == SimCommand.INITIALIZE:
                # Reset ship with optional new configuration
                new_config = SimulationConfig(**params) if params else self.config
                self.simulation = ShipSimulation(
                    width_slots=new_config.width_slots,
                    height_slots=new_config.height_slots,
                    container_width=new_config.container_width,
                    container_height=new_config.container_height,
                    logger=self.logger
                )
                response["message"] = "Ship reinitialized"
                # Publish initial telemetry after initialization
                await self.publish_telemetry()

            elif command == SimCommand.DUMP_STATE:
                # Get current simulation state
                state = self.get_simulation_state()
                await self.connectivity.publish(
                    f"state/ship/{self.connectivity.client_id}/state",
                    json.dumps(state)
                )
                response["message"] = "State dumped to state topic"

            elif command == SimCommand.EMERGENCY:
                self.emergency_mode = True
                await self.connectivity.publish_status({
                    "operational_status": "ERROR",
                    "message": "Emergency mode activated"
                })
                response["message"] = "Emergency mode activated"

            elif command == SimCommand.CLEAR_EMERGENCY:
                self.emergency_mode = False
                await self.connectivity.publish_status({
                    "operational_status": "READY",
                    "message": "Emergency mode cleared"
                })
                response["message"] = "Emergency mode cleared"

            # Publish command response
            await self.connectivity.publish(
                f"control/ship/{self.connectivity.client_id}/response",
                json.dumps(response)
            )

        except ValueError as e:
            # Invalid command
            await self.connectivity.publish(
                f"ship/{self.connectivity.client_id}/control/response",
                json.dumps({
                    "command": payload.get("command"),
                    "status": "error",
                    "message": f"Invalid command: {str(e)}"
                })
            )

    def get_simulation_state(self):
        """Get complete simulation state"""
        return {
            "config": vars(self.config),
            "status": {
                "emergency_mode": self.emergency_mode
            },
            "ship_state": {
                "container_grid": self.simulation.grid.tolist(),
                "telemetry": self.simulation.get_telemetry()
            }
        }

    async def publish_telemetry(self):
        """Publish current telemetry data"""
        telemetry = self.simulation.get_telemetry()
        await self.connectivity.publish_telemetry(telemetry)

