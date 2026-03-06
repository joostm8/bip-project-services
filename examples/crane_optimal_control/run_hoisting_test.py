from pathlib import Path
import sys
from time import sleep

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from TMC4671_printer.motors import HoistStepper
from mqtt_crane.gantry_system.hoisting_test import hoist


def run() -> None:
    hs = HoistStepper(port="COM10", calibrated=True)
    print(hoist(hs, 0.15))
    sleep(1)
    print(hoist(hs, 0))


if __name__ == "__main__":
    run()
