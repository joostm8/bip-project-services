from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crane_optimal_control.mqtt_gantry_controller import ControllerMQTTWrapper


def run(mock: bool = True) -> None:
    config_path = ROOT / "src" / "crane_optimal_control" / "gantry_system" / "crane-properties.yaml"
    wrapper = ControllerMQTTWrapper(str(config_path), mock=mock)
    wrapper.start()


if __name__ == "__main__":
    run()
