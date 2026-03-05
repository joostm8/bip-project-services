from pathlib import Path
import sys
import logging
from time import sleep
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crane_optimal_control.gantry_system.gantry_controller import PhysicalGantryController


def run() -> None:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    config_path = ROOT / "src" / "crane_optimal_control" / "gantry_system" / "crane-properties.yaml"

    with PhysicalGantryController(str(config_path)) as gc:
        print(gc.hoist(0.3))
        sleep(2)
        traj, meas = gc.moveWithoutLog(0.45, generator="ocp")
        sleep(2)
        print(gc.hoist(0))
        sleep(2)
        if type(gc) is PhysicalGantryController:
            gc.printer.gantryStepper.setPositionMode()
            gc.printer.gantryStepper.setPosition(0)
            gc.printer.gantryStepper.setVelocityLimit(6000)
        plt.show()
        print(gc.printer.gantryStepper.mm_s_to_rpm)


if __name__ == "__main__":
    run()
