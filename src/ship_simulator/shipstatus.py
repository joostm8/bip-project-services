from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time

class OperationalStatus(Enum):
    READY = "READY"
    LOADING = "LOADING"
    FULL = "FULL"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"

class SafetyStatus(Enum):
    STABLE = "STABLE"
    WARNING_HEEL = "WARNING_HEEL"
    WARNING_DRAFT = "WARNING_DRAFT"
    WARNING_STABILITY = "WARNING_STABILITY"
    CRITICAL = "CRITICAL"

@dataclass
class ShipStatus:
    operational_status: OperationalStatus
    safety_status: SafetyStatus
    timestamp: float
    message: Optional[str] = None
    
    def to_dict(self):
        return {
            "operational_status": self.operational_status.value,
            "safety_status": self.safety_status.value,
            "timestamp": self.timestamp,
            "message": self.message
        }


def determine_operational_status(safety_status: SafetyStatus) -> OperationalStatus:
    """Determine operational status based on safety status"""
    if safety_status == SafetyStatus.CRITICAL:
        return OperationalStatus.ERROR
    elif safety_status in [SafetyStatus.WARNING_HEEL,
                         SafetyStatus.WARNING_DRAFT,
                         SafetyStatus.WARNING_STABILITY]:
        return OperationalStatus.READY  # Still accepting containers but with caution
    else:
        return OperationalStatus.READY


class StatusManager:
    def __init__(self, connectivity):
        self.connectivity = connectivity
        self.current_status = ShipStatus(
            operational_status=OperationalStatus.READY,
            safety_status=SafetyStatus.STABLE,
            timestamp=time.time()
        )
        
        # Define safety thresholds
        self.thresholds = {
            'max_heel_angle': 5.0,  # degrees
            'warning_heel_angle': 3.0,  # degrees
            'min_gm': 0.5,  # meters
            'optimal_gm': 2.0,  # meters
            'max_draft_percentage': 95,  # percentage of design draft
            'warning_draft_percentage': 85  # percentage of design draft
        }

    async def update_status_from_telemetry(self, telemetry_data):
        """Update ship status based on telemetry data"""
        new_safety_status = SafetyStatus.STABLE
        messages = []

        # Check heel angle
        if abs(telemetry_data['heel_angle']) > self.thresholds['max_heel_angle']:
            new_safety_status = SafetyStatus.CRITICAL
            messages.append(f"Critical heel angle: {telemetry_data['heel_angle']:.1f}°")
        elif abs(telemetry_data['heel_angle']) > self.thresholds['warning_heel_angle']:
            new_safety_status = SafetyStatus.WARNING_HEEL
            messages.append(f"High heel angle: {telemetry_data['heel_angle']:.1f}°")

        # Check GM distance
        if telemetry_data['GM'] < self.thresholds['min_gm']:
            new_safety_status = SafetyStatus.CRITICAL
            messages.append(f"Critical GM distance: {telemetry_data['gm_distance']:.2f}m")
        elif telemetry_data['GM'] < self.thresholds['optimal_gm']:
            if new_safety_status != SafetyStatus.CRITICAL:
                new_safety_status = SafetyStatus.WARNING_STABILITY
            messages.append(f"Low GM distance: {telemetry_data['gm_distance']:.2f}m")

        # Check draft
        design_draft = 12.0  # meters (from ship simulation)
        draft_percentage = (telemetry_data['draught'] / design_draft) * 100
        if draft_percentage > self.thresholds['max_draft_percentage']:
            new_safety_status = SafetyStatus.CRITICAL
            messages.append(f"Critical draft: {telemetry_data['draught']:.2f}m")
        elif draft_percentage > self.thresholds['warning_draft_percentage']:
            if new_safety_status != SafetyStatus.CRITICAL:
                new_safety_status = SafetyStatus.WARNING_DRAFT
            messages.append(f"High draft: {telemetry_data['draught']:.2f}m")

        # Update status if changed
        if (new_safety_status != self.current_status.safety_status or 
            len(messages) > 0):
            self.current_status = ShipStatus(
                operational_status=determine_operational_status(new_safety_status),
                safety_status=new_safety_status,
                timestamp=time.time(),
                message=" | ".join(messages) if messages else None
            )
            await self.connectivity.publish_status(self.current_status.to_dict())

    async def set_loading_status(self):
        """Set status to LOADING when processing a container"""
        self.current_status = ShipStatus(
            operational_status=OperationalStatus.LOADING,
            safety_status=self.current_status.safety_status,
            timestamp=time.time(),
            message="Processing container request"
        )
        await self.connectivity.publish_status(self.current_status.to_dict())

    async def set_maintenance_status(self, message: str = "Scheduled maintenance"):
        """Set status to MAINTENANCE"""
        self.current_status = ShipStatus(
            operational_status=OperationalStatus.MAINTENANCE,
            safety_status=self.current_status.safety_status,
            timestamp=time.time(),
            message=message
        )
        await self.connectivity.publish_status(self.current_status.to_dict())

    async def set_error_status(self , e):
        """Set status to ERROR"""
        self.current_status = ShipStatus(operational_status=OperationalStatus.ERROR,
            safety_status=self.current_status.safety_status,
            timestamp=time.time(),
            message=e
        )
        await self.connectivity.publish_status(self.current_status.to_dict())