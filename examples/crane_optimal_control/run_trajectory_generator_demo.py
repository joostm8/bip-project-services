from pathlib import Path
import sys
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mqtt_crane.gantry_system.trajectory_generator import TrajectoryGenerator


def run() -> None:
    config_path = ROOT / "src" / "crane_optimal_control" / "gantry_system" / "crane-properties.yaml"
    tg = TrajectoryGenerator(str(config_path))
    t, x, dx, ddx, theta, omega, alpha, u = tg.generateTrajectory(0, 0.65)
    print("dt:")
    print(t[1:-1] - t[0:-2])
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.plot(t, x)
    ax1.plot(t, dx)
    ax2.plot(t, ddx)
    plt.show()


if __name__ == "__main__":
    run()
