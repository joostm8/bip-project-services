from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ship_simulator.container import Container
from ship_simulator.shipsimulation import ShipSimulation


def print_stability_snapshot(simulation: ShipSimulation, label: str) -> None:
    heel_angle, heeled_stability = simulation.calculate_equilibrium_heel()
    upright_stability = simulation.calculate_stability_at_heel(0)
    draught, draught_info = simulation.calculate_draught()

    print(f"\n--- {label} ---")
    print(f"Total ship weight: {draught_info['total_weight'] / 1000:.1f} tons")
    print(f"Draught: {draught:.2f} m ({draught_info['load_percentage']:.1f}% of design)")
    print(f"Equilibrium heel: {heel_angle:.2f} deg")
    print(f"GM upright: {upright_stability['GM']:.2f} m")
    print(f"GM at equilibrium: {heeled_stability['GM']:.2f} m")
    print(f"Righting moment: {heeled_stability['righting_moment'] / 1000:.1f} kN*m")


def run() -> None:
    # 3 columns x 2 rows container grid
    simulation = ShipSimulation(width_slots=3, height_slots=2)

    print("ShipSimulation plain demo (no MQTT)")
    print("Grid: 3 columns x 2 rows")

    print_stability_snapshot(simulation, "Initial condition (empty grid)")

    # Load container 1 on the port side (left column)
    c1 = Container(weight=24_000, container_id="C-001")
    success, message, heel_angle = simulation.process_container_add(c1, x_slot=0, y_slot=0)
    print(f"\nLoad C-001 at (x=0, y=0): {message}")
    if not success:
        raise RuntimeError(f"Failed to add C-001: {message}")
    print(f"Reported heel after add: {heel_angle:.2f} deg")
    print_stability_snapshot(simulation, "After loading first container")

    # Load container 2 on starboard side (right column) to rebalance
    c2 = Container(weight=26_000, container_id="C-002")
    success, message, heel_angle = simulation.process_container_add(c2, x_slot=2, y_slot=0)
    print(f"\nLoad C-002 at (x=2, y=0): {message}")
    if not success:
        raise RuntimeError(f"Failed to add C-002: {message}")
    print(f"Reported heel after add: {heel_angle:.2f} deg")
    print_stability_snapshot(simulation, "After loading second container")

    print("\nFinal telemetry dict:")
    print(simulation.get_telemetry())


if __name__ == "__main__":
    run()