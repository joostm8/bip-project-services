from minimal_example import MinimalExample
from direct_database_writer import DirectDatabaseWriter


def run() -> None:
    example = MinimalExample(id=1)
    example.waitForRetained()
    dbw = DirectDatabaseWriter(1)
    dbw.setShipRoll(example.response["heel_angle"])
    dbw.setShipDraft(example.response["draught"])

    container_id = dbw.getContainerInShipSlot(0)
    container_pos = dbw.getShipSlotPosition(0)
    weight = dbw.getContainerWeight(container_id)
    example.updateShipSimulation(container_id, container_pos, weight)
    dbw.setShipRoll(example.response["heel_angle"])
    dbw.setShipDraft(example.response["draught"])


if __name__ == "__main__":
    run()
