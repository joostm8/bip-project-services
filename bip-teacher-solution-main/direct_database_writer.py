"""
Class with a bunch of functions to write directly to the database.
"""
import psycopg

class DirectDatabaseWriter:

    def __init__(self, group_id):
        self.id = group_id
        try:
            connectstring = "host=localhost dbname=gantrycrane \
                            user=postgres password=postgres"
            self.dbconn = psycopg.connect(connectstring)
        except Exception as e:
            print(e)

    def _dbWrite(self, query):
        with self.dbconn.cursor() as cur:
            cur.execute(query)
            self.dbconn.commit()


    def _dbRead(self, query):
        with self.dbconn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
        
    def getShipFillableSlots(self):
        """
        Gets the fillable slots of the cargomanifest

        returns a list of tuples of the form (slot, container_id)
        """
        query = f"SELECT slot, container_id FROM cargomanifest WHERE \
            ship_id = {self.id} and state = 'fillable';"
        return self._dbRead(query)

    def getShipSlotPosition(self, slot):
        """
        Gets the position of a slot on the ship

        returns a tuple (pos_x, pos_y)
        """
        query = f"SELECT pos_x, pos_y FROM cargomanifest WHERE \
            ship_id = {self.id} and slot = {slot};"
        return self._dbRead(query)[0]
    
    def setShipSlotState(self, slot, newState):
        """
        Updates a slot's state.

        newSate should be 'empty', 'fillable' or 'filled'
        """
        query = f"UPDATE cargomanifest SET state = '{newState}' WHERE \
            slot = {slot} and ship_id = {self.id};"
        self._dbWrite(query)

    def getShipSlotState(self, slot):
        """
        Gets a slot's state.

        returns 'empty', 'fillable' or 'filled'
        """
        query = f"SELECT state FROM cargomanifest WHERE \
            ship_id = {self.id} and slot = {slot};"
        return self._dbRead(query)[0][0]
    
    def getContainerInShipSlot(self, slot):
        """
        Gets a slot's state.

        returns 'empty', 'fillable' or 'filled'
        """
        query = f"SELECT container_id FROM cargomanifest WHERE \
            ship_id = {self.id} and slot = {slot};"
        return self._dbRead(query)[0][0]

    def getContainerWeight(self, container):
        """
        Gets a container's weight

        returns the container's weight
        """
        query = f"SELECT weight FROM container WHERE \
            container_id = {container};"
        return self._dbRead(query)[0][0]
    
    def getQuayFillableSlots(self):
        """
        Gets the fillable slots of the cargomanifest

        returns a list of tuples of the form (slot, container_id)
        """
        query = f"SELECT slot, container_id FROM quay WHERE \
            machine_id = {self.id} and state = 'fillable';"
        return self._dbRead(query)
    
    def getQuayFilledSlots(self):
        """
        Gets the filled slots of the quay

        returns a list of tuples of the form (slot, container_id)
        """
        query = f"SELECT slot, container_id FROM quay WHERE \
            machine_id = {self.id} and state = 'filled';"
        return self._dbRead(query)

    def getQuaySlotPosition(self, slot):
        """
        Gets the position of a slot on the ship

        returns a tuple (pos_x, pos_y)
        """
        query = f"SELECT pos_x, pos_y FROM quay WHERE \
            machine_id = {self.id} and slot = {slot};"
        return self._dbRead(query)[0]
    
    def setQuaySlotState(self, slot, newState):
        """
        Updates a slot's state.

        newSate should be 'empty', 'fillable' or 'filled'
        """
        query = f"UPDATE quay SET state = '{newState}' WHERE \
            slot = {slot} and machine_id = {self.id};"
        self._dbWrite(query)

    def getQuaySlotState(self, slot):
        """
        Gets a slot's state.

        returns 'empty', 'fillable' or 'filled'
        """
        query = f"SELECT state FROM quay WHERE \
            machine_id = {self.id} and slot = {slot};"
        return self._dbRead(query)[0][0]
    
        
    def getContainerInQuaySlot(self, slot):
        """
        Gets the container id that is in a slot.

        returns the container id.
        """
        query = f"SELECT container_id FROM quay WHERE \
            machine_id = {self.id} and slot = {slot};"
        return self._dbRead(query)[0][0]

    def setShipRoll(self, roll):
        """
        Updates a ship's roll.
        """
        query = f"UPDATE ship SET roll = {roll} WHERE id = {self.id};"
        self._dbWrite(query)

    def getShipRoll(self):
        """
        Gets the ship's roll
        """
        query = f"SELECT roll FROM ship WHERE id = {self.id};"
        return self._dbRead(query)[0][0]
    
    def setShipDraft(self, draft):
        """
        Updates a ship's roll.
        """
        query = f"UPDATE ship SET draft = {draft} WHERE id = {self.id};"
        self._dbWrite(query)

    def getShipDraft(self):
        """
        Gets the ship's draft

        returns the ship's draft
        """
        query = f"SELECT draft FROM ship WHERE id = {self.id};"
        return self._dbRead(query)[0][0]
    
    def resetShip(self):
        """
        Reset the Quay (all slots empty, bottom row fillable)
        """
        query = f"UPDATE cargomanifest SET state = 'empty' WHERE \
            ship_id = {self.id};"
        self._dbWrite(query)
        query = f"UPDATE cargomanifest SET state = 'fillable' WHERE \
            ship_id = {self.id} and slot in (0, 5, 10, 15, 20);"
        self._dbWrite(query)

    def resetQuay(self):
        """
        Reset the ship (all slots empty, bottom row fillable.)
        """
        query = f"UPDATE quay SET state = 'empty' WHERE \
            machine_id = {self.id};"
        self._dbWrite(query)
        query = f"UPDATE quay SET state = 'fillable' WHERE \
            machine_id = {self.id} and slot in (0, 3, 6, 12, 18);"
        self._dbWrite(query)

if __name__ == "__main__":
    dbw = DirectDatabaseWriter(1)
    # do some test queries.
    print(dbw.getShipFillableSlots())
    print(dbw.getShipSlotPosition(5))
    dbw.setShipSlotState(3, 'empty')
    print(dbw.getShipSlotState(3))
    print(dbw.getContainerWeight(5))
    print(dbw.getQuayFillableSlots())
    print(dbw.getQuaySlotPosition(5))
    dbw.setQuaySlotState(2, 'empty')
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
    