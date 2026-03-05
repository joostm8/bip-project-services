from pathlib import Path
import sys
import asyncio
import logging

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ship_simulator.shipsimulationmain import ShipSimulationSystem


async def main() -> None:
    simulation = ShipSimulationSystem(
        broker="localhost",
        port=1883,
        ship_id="1",
        username="shipsim",
        password="shipsim",
    )

    try:
        await simulation.start()
    except KeyboardInterrupt:
        await simulation.stop()
    except Exception as exc:
        logging.error(f"Fatal error: {str(exc)}")
        await simulation.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
