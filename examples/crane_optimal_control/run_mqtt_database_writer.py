from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crane_optimal_control.mqtt_database_writer import DatabaseMQTTWrapper


def run() -> None:
    config_path = ROOT / "src" / "crane_optimal_control" / "gantry_system" / "crane-properties.yaml"
    wrapper = DatabaseMQTTWrapper(config_path=str(config_path))
    wrapper.start()


if __name__ == "__main__":
    run()
