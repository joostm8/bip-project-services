import numpy as np
from container import Container
import logging


class ShipSimulation:
    def __init__(self, width_slots, height_slots, container_width=2.4, container_height=2.6):
        # Previous initialization code remains the same
        self.width_slots = width_slots
        self.height_slots = height_slots
        self.container_width = container_width
        self.container_height = container_height
        self.total_width = width_slots * container_width
        self.total_height = height_slots * container_height
        self.grid = np.full((height_slots, width_slots), None)
        self.logger = logging.getLogger(__name__)

        # Coordinate systems
        self.x_coords = np.linspace(
            -(self.total_width / 2) + (container_width / 2),
            (self.total_width / 2) - (container_width / 2),
            width_slots
        )
        self.y_coords = np.linspace(
            0 + (container_height / 2),
            self.total_height - (container_height / 2),
            height_slots
        )

       # self.hull_width = 30.0  # meters (beam)
        self.hull_width = 30
        self.hull_length = 180.0  # meters
        self.water_density = 1025  # kg/m³ (seawater density)
        self.block_coefficient = 0.6
        self.hull_center_of_mass = (0, self.total_height * 0.42)

        # Standard container length
        self.container_length = 6.1  # meters

        # Calculate how many containers fit along ship's length
        self.length_slots = int(self.hull_length / self.container_length)

        self.hull_weight = 8_000_000  # 15,000 tons in kg

        # Add stability-related parameters
        self.bm_coefficient = 0.084  # Used to calculate BM based on ship width and draught

        # Critical GM values (in meters)
        self.critical_gm = 0.5  # Minimum recommended GM
        self.optimal_gm = 2.0  # Optimal GM for container ships

        self.g = 9.81  # gravitational acceleration m/s²

        # Add fault injection related attributes
        self.fault_injection_enabled = False
        self.faulty_containers = {}  # Dictionary to store faulty container weights
        self.positions_injected = np.full((height_slots, width_slots), None)
        self.faulty_positions = {
            (height_slots - 1, 0),  # Top slot
            (height_slots - 2, 0), # Second from top
            (height_slots - 3,0)
        }
        self.faulty_modifier = 2.3

    def enable_fault_injection(self):
        """Enable fault injection mode"""
        self.fault_injection_enabled = True
        if self.logger is not None:
            self.logger.info("Fault injection enabled")

    def disable_fault_injection(self):
        """Disable fault injection mode"""
        self.fault_injection_enabled = False
        self.faulty_containers.clear()  # Clear stored faulty container data
        self.fault_injected_positions.clear()  # Clear the record of injected positions
        if self.logger is not None:
            self.logger.info("Fault injection disabled")

    def _inject_fault(self, container: Container) -> Container:
        """
        Inject fault by increasing container weight by 20%
        Returns a new container with modified weight
        """
        faulty_weight = int(container.weight * self.faulty_modifier)
        return Container(weight=faulty_weight, container_id=container.container_id)

    def calculate_kb_ratio(self):
        """
        Calculate KB ratio based on block coefficient.
        For V-shaped hulls (low Cb), KB should be lower.
        """
        # More realistic relationship
        kb_ratio = 0.45 + (0.15 * self.block_coefficient)
        return kb_ratio

    def calculate_kb(self, draught):
        """
        Calculate KB (height of center of buoyancy)
        """
        kb_ratio = self.calculate_kb_ratio()
        return kb_ratio * draught

    def calculate_center_of_mass(self):
        """
        Calculate the center of mass for the entire ship including hull and containers.
        Returns: tuple (x, y) representing the center of mass coordinates
        """
        total_mass = self.hull_weight
        mass_moment_x = self.hull_weight * self.hull_center_of_mass[0]
        mass_moment_y = self.hull_weight * self.hull_center_of_mass[1]

        # Add contribution from each container
        for y_idx in range(self.height_slots):
            for x_idx in range(self.width_slots):
                container = self.grid[y_idx, x_idx]
                if container is not None:
                    x_pos = self.x_coords[x_idx]
                    y_pos = self.y_coords[y_idx]

                    total_mass += container.weight
                    mass_moment_x += container.weight * x_pos
                    mass_moment_y += container.weight * y_pos

        # Calculate center of mass coordinates
        if total_mass == 0:
            return self.hull_center_of_mass  # Return hull COM if ship is empty
        else:
            com_x = mass_moment_x / total_mass
            com_y = mass_moment_y / total_mass
            return (com_x, com_y)

    def get_total_weight(self):
        """
        Calculate total weight considering containers extended along ship's length (otherwise it is going to be difficult to get an unstable ship)
        """
        # Start with hull weight
        total_weight = self.hull_weight

        # For each container in the grid, multiply its weight by the number of length slots
        for y_idx in range(self.height_slots):
            for x_idx in range(self.width_slots):
                container = self.grid[y_idx, x_idx]
                if container is not None:
                    # Each container position represents a full row along the ship's length
                    total_weight += container.weight * self.length_slots

        return total_weight

    def calculate_draught(self):
        """
        Calculate the ship's draught based on total weight and water displacement.
        """
        total_weight = self.get_total_weight()  # in kg

        # Calculate required displacement volume (m³)
        required_volume = total_weight / self.water_density

        # Calculate draught
        draught = required_volume / (self.hull_length * self.hull_width * self.block_coefficient)

        # Calculate additional information
        design_draught = 12.0  # meters
        load_percentage = (draught / design_draught) * 100

        info = {
            'draught': draught,
            'displacement_volume': required_volume,
            'design_draught': design_draught,
            'load_percentage': load_percentage,
            'total_weight': total_weight,
            'containers_per_row': self.length_slots
        }

        return draught, info

    def print_loading_info(self):
        """Print detailed loading information"""
        draught, info = self.calculate_draught()
        total_containers = 0
        total_container_weight = 0

        for y_idx in range(self.height_slots):
            for x_idx in range(self.width_slots):
                if self.grid[y_idx, x_idx] is not None:
                    total_containers += self.length_slots
                    total_container_weight += self.grid[y_idx, x_idx].weight * self.length_slots

        print("\n=== Ship Loading Information ===")
        print(f"Ship Length: {self.hull_length:.1f} m")
        print(f"Containers per length: {self.length_slots}")
        print(f"Total container positions: {total_containers}")
        print(f"Total container weight: {total_container_weight / 1000:.0f} tons")
        print(f"Hull weight: {self.hull_weight / 1000:.0f} tons")
        print(f"Total ship weight: {info['total_weight'] / 1000:.0f} tons")
        print(f"Current draught: {draught:.2f} m")
        print(f"Load percentage: {info['load_percentage']:.1f}%")

    def calculate_heel_angle(self):
        """
        Calculate the heel angle based on the current loading condition.
        Uses the principle: tan(θ) = heeling_moment / (displacement * GM)
        This is an approximate solution, that makes a quick estimate.
        There is another function to make an iterative approach to finding the correct heel angle
        Returns heel angle in degrees
        """
        stability = self.calculate_stability_at_heel(0)
        gm = stability['GM']

        # Calculate the moment caused by containers
        total_moment = 0
        displacement = self.get_total_weight()

        for y_idx in range(self.height_slots):
            for x_idx in range(self.width_slots):
                container = self.grid[y_idx, x_idx]
                if container is not None:
                    # Distance from centerline
                    x_distance = self.x_coords[x_idx]
                    # Calculate moment for entire row of containers
                    weight = container.weight * self.length_slots
                    moment = weight * x_distance * self.g  # Newton-meters
                    total_moment += moment

        # Calculate heel angle
        if gm > 0:
            # theta = arctan(heeling_moment / (displacement * GM))
            heel_angle = np.arctan(total_moment / (displacement * gm * self.g))
            heel_degrees = np.rad2deg(heel_angle)
        else:
            heel_degrees = float('inf')  # Indicates instability

        return heel_degrees, {
            'total_moment': total_moment,
            'gm': gm,
            'displacement': displacement
        }

    def calculate_heel_for_new_container(self, container, x_slot, y_slot):
        """
        Calculate what the heel angle would be if a container was added at the specified position
        Returns the predicted heel angle without actually adding the container
        """
        # Temporarily add the container
        original_container = self.grid[y_slot, x_slot]
        self.grid[y_slot, x_slot] = container

        # Calculate new heel
        new_heel, info = self.calculate_heel_angle()

        # Restore original state
        self.grid[y_slot, x_slot] = original_container

        return new_heel, info

    def process_container_add(self, container, x_slot, y_slot, max_heel_angle=5.0):
        """
        Try to add a container and check if resulting heel angle is acceptable
        Returns: (success, message, heel_angle)
        """
        # First check if position is valid
        is_valid, message = self.is_valid_placement(x_slot, y_slot)
        if not is_valid:
            return False, message, 0.0

        # Check if this container should have fault injection
        position = (y_slot, x_slot)
        container_to_add = container
        print(container_to_add.container_id in self.faulty_containers.keys())
        if (self.fault_injection_enabled and
                position in self.faulty_positions and
                self.positions_injected[y_slot,x_slot] is None):
            # This is a container where we should inject a fault and haven't done so yet
            container_to_add = self._inject_fault(container)
            self.positions_injected[y_slot,x_slot] = "INJECTED"
            print(self.positions_injected)
            self.faulty_containers[container.container_id] = container_to_add.weight
            print(self.faulty_containers)
            if self.logger is not None:
                self.logger.info(f"Fault injected for container {container.container_id} at position {position}. "
                             f"Original weight: {container.weight}, New weight: {container_to_add.weight}")
        elif container_to_add.container_id in self.faulty_containers.keys():
            # Container was previously fault injected, use stored weight
            container_to_add = Container(
                weight=self.faulty_containers[container.container_id],
                container_id=container.container_id
            )
            if self.logger is not None:
                self.logger.info(f"Using stored faulty weight for container {container.container_id}: "
                             f"{container_to_add.weight}")

        # Add the container (either original or fault-injected)
        self.grid[y_slot, x_slot] = container_to_add

        # Calculate new heel angle
        heel_angle, _ = self.calculate_heel_angle()

        return True, f"Container added. New heel angle: {heel_angle:.1f}°", heel_angle

    def process_container_remove(self, x_slot, y_slot):
        # Check if there is a container on x_y
        if self.grid[y_slot, x_slot] is None:
            return False, "Position empty", None, None
        # Check if the container is accessible
        if not self.is_highest_on_column(y_slot, x_slot):
            return False, "Position not accessible", None, None
        # Remove the container
        removed  = self.grid[y_slot, x_slot]
        self.grid[y_slot, x_slot] = None
        # Do Analysis
        heel_angle, stability = self.calculate_equilibrium_heel()
        return True, f"Container removed. New heel angle: {heel_angle:.1f}°", heel_angle, removed

    def calculate_stability_at_heel(self, heel_angle_deg):
        """
        Calculate stability parameters for a given heel angle
        """
        heel_rad = np.deg2rad(heel_angle_deg)
        draught, _ = self.calculate_draught()

        # Calculate new waterplane area and moment of inertia
        # When ship heels, the waterplane becomes asymmetric
        cos_heel = np.cos(heel_rad)
        sin_heel = np.sin(heel_rad)

        # New effective beam at waterline
        effective_beam = self.hull_width * cos_heel

        # Calculate reduction in waterplane area due to heel
        # This is a simplified approximation - real ships have more complex hull shapes
        waterplane_area = self.hull_length * effective_beam

        # Calculate new second moment of area (I)
        # This changes significantly with heel
        I = (self.hull_length * effective_beam ** 3) / 12

        # Calculate new displaced volume
        # This stays roughly constant but shape changes
        displaced_volume = self.get_total_weight() / self.water_density

        # Calculate new KB
        # KB increases with heel angle due to shape change
        # This is an approximation - real value depends on hull form
        kb_base = self.calculate_kb(draught)
        kb_increase = draught * (1 - cos_heel) * 0.5
        kb = kb_base + kb_increase

        # Calculate new BM
        # BM decreases with heel due to reduced effective waterplane area
        bm = I / displaced_volume if displaced_volume > 0 else 0

        # Calculate center of gravity height (KG)
        com = self.calculate_center_of_mass()
        kg = com[1] + draught

        # Calculate GZ (righting arm) for this heel angle
        # GZ = GM * sin(θ) + additional terms for large angles
        gm = kb + bm - kg
        gz_first_order = gm * sin_heel

        # Add correction for large angles (wall-sided formula)
        # This accounts for the change in waterplane shape
        wall_sided_correction = -0.5 * self.hull_width * sin_heel ** 2 / displaced_volume
        gz = gz_first_order + wall_sided_correction

        # Calculate righting moment
        righting_moment = gz * self.get_total_weight() * self.g

        return {
            'KB': kb,
            'BM': bm,
            'KG': kg,
            'GM': gm,
            'GZ': gz,
            'righting_moment': righting_moment,
            'effective_beam': effective_beam,
            'waterplane_area': waterplane_area,
            'heel_angle': heel_angle_deg
        }

    def calculate_equilibrium_heel(self):
        """
        this is a more accurate version (less approximate) of the calculate_heel_angle function
        It iteratively updates the GM value as the ship heels
        It adjusts the heeling moments by accounting for the cosine effect of heel
        It keeps iterating until it finds a stable solution where all forces balance
        Iteratively find the equilibrium heel angle where heeling moment equals righting moment
        """
        max_iterations = 30
        tolerance = 0.1  # degrees
        stability = 0
        heel_angle = 0
        for _ in range(max_iterations):
            # Calculate stability at current heel
            stability = self.calculate_stability_at_heel(heel_angle)

            # Calculate heeling moment from container weights
            total_heeling_moment = 0
            for y_idx in range(self.height_slots):
                for x_idx in range(self.width_slots):
                    container = self.grid[y_idx, x_idx]
                    if container is not None:
                        # Adjust x-coordinate for heel
                        x_distance = self.x_coords[x_idx] * np.cos(np.deg2rad(heel_angle))
                        weight = container.weight * self.length_slots
                        moment = weight * x_distance * self.g
                        total_heeling_moment += moment

            # Calculate new heel angle
            # For small angles: heel ≈ heeling_moment / (displacement * GM)
            new_heel = np.rad2deg(np.arctan(total_heeling_moment /
                                            (self.get_total_weight() * self.g * stability['GM'])))

            # Check convergence
            if abs(new_heel - heel_angle) < tolerance:
                return new_heel, stability

            heel_angle = (heel_angle + new_heel) / 2  # Take average for stability

        return heel_angle, stability

    def print_stability_analysis(self):
        """Print comprehensive stability analysis including heeled condition"""
        heel_angle, heeled_stability = self.calculate_equilibrium_heel()
        upright_stability = self.calculate_stability_at_heel(0)

        print("\n=== Detailed Stability Analysis ===")
        print("\nUpright Condition:")
        print(f"GM: {upright_stability['GM']:.2f}m")
        print(f"KB: {upright_stability['KB']:.2f}m")
        print(f"BM: {upright_stability['BM']:.2f}m")

        print("\nHeeled Condition:")
        print(f"Equilibrium heel angle: {heel_angle:.2f}°")
        print(f"GM: {heeled_stability['GM']:.2f}m")
        print(f"KB: {heeled_stability['KB']:.2f}m")
        print(f"BM: {heeled_stability['BM']:.2f}m")
        print(f"GZ: {heeled_stability['GZ']:.2f}m")
        print(f"Righting moment: {heeled_stability['righting_moment'] / 1000:.1f} kN·m")
        print(f"Effective beam: {heeled_stability['effective_beam']:.2f}m")

    def is_highest_on_column(self, y, x):
        """Function assumes that it is checked that there is a container in the slot """
        if y == self.height_slots-1:
            return True
        if self.grid[y+1][x] is None:
            return True
        return False

    def is_valid_placement(self, x_slot, y_slot):
        """
        Check if a container can be placed at the given position.
        Rules:
        1. Position must be within grid bounds
        2. Position must be empty
        3. Position must be at bottom or have container below it
        """
        # Check if position is within bounds
        if not (0 <= x_slot < self.width_slots and 0 <= y_slot < self.height_slots):
            return False, "Position out of bounds"

        # Check if position is already occupied
        if self.grid[y_slot, x_slot] is not None:
            return False, "Position already occupied"

        # Check if it's the bottom level (y_slot = 0)
        if y_slot == 0:
            return True, "Valid bottom position"

        # Check if there's a container below
        if self.grid[y_slot - 1, x_slot] is None:
            return False, "No supporting container below"

        return True, "Valid position"

    def find_next_valid_position(self, x_slot):
        """
        Find the next valid height position for a given x coordinate.
        Returns None if column is full.
        """
        for y_slot in range(self.height_slots):
            is_valid, _ = self.is_valid_placement(x_slot, y_slot)
            if is_valid:
                return y_slot
        return None

    def get_telemetry(self):
        heel_angle, heeled_stability = self.calculate_equilibrium_heel()
        draft, draftinfo = self.calculate_draught()
        heeled_stability['draught'] = draft
        return heeled_stability

