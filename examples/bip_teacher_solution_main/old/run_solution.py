from time import sleep
from examples.bip_teacher_solution_main.old.solution import (
    BipTeacherSolution,
    MOVE_HEIGHT,
    PICKUP_HEIGHT,
    PICKUP_POSITION,
    CONTAINER_HEIGHT,
    SHIP_HEIGHT,
    SHIP_POSITIONS,
)


def run() -> None:
    sol = BipTeacherSolution()

    while True:
        scanned_id = sol.scanContainer()
        while not scanned_id:
            scanned_id = sol.scanContainer()
            print("no id was scanned, try rotating the container")
            sleep(1)

        print(f"Scanned container with id: {scanned_id}")
        if scanned_id == sol.loadingorder[0]:
            print("Container can be loaded")
            print(f"Loading position is{sol.container_positions[scanned_id]}")
            container_position = sol.container_positions[scanned_id - 1]
            sol.hoistCrane(MOVE_HEIGHT)
            sol.moveCrane(PICKUP_POSITION)
            sol.hoistCrane(PICKUP_HEIGHT)
            sol.electromagnet(True)
            sleep(1)
            sol.hoistCrane(MOVE_HEIGHT)
            sol.moveCrane(SHIP_POSITIONS[container_position[0]])
            sol.hoistCrane(SHIP_HEIGHT + CONTAINER_HEIGHT * (container_position[1] + 1))
            sol.electromagnet(False)
            sol.hoistCrane(MOVE_HEIGHT)
            sol.removeFromLoadingOrder()
        elif scanned_id in sol.loadingorder:
            print(
                f"Container {scanned_id} is in the loading list, but would be loaded too early, please present it again later"
            )
            sol.rejectContainer()
            input("Please unload the container and press any key to continue...")
        else:
            print(f"Container {scanned_id} is not in the loading manifest and is rejected")
            sol.rejectContainer()
            input("Please unload the container and press any key to continue...")


if __name__ == "__main__":
    run()
