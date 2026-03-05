from direct_database_writer import DirectDatabaseWriter


def run() -> None:
    dbw = DirectDatabaseWriter(1)
    print(dbw.getShipFillableSlots())
    print(dbw.getShipSlotPosition(5))
    dbw.setShipSlotState(3, "empty")
    print(dbw.getShipSlotState(3))
    print(dbw.getContainerWeight(5))
    print(dbw.getQuayFillableSlots())
    print(dbw.getQuaySlotPosition(5))
    dbw.setQuaySlotState(2, "empty")
    print(dbw.getQuaySlotState(2))
    print(dbw.getQuayFilledSlots())
    draft = dbw.getShipDraft()
    print(draft)
    dbw.setShipDraft(draft + 1)
    print(dbw.getShipRoll())
    roll = dbw.getShipRoll()
    print(roll)
    dbw.setShipRoll(draft + 1)
    print(dbw.getShipRoll())
    print(dbw.getContainerInQuaySlot(0))
    print(dbw.getContainerInShipSlot(0))
    dbw.resetShip()
    dbw.resetQuay()


if __name__ == "__main__":
    run()
