from TMC4671_printer.motors import HoistStepper
from time import sleep
    
def hoist(hs, pos):
    """
    Hoists to target position (in meters)

    returns the exact final position
    """
    # inverts direction.
    hs.setPosition(int(262144 - hs.mm_to_counts * pos * 1000))
    #while(round(self.printer.hoistStepper.getPosition(), 3))
    sleep(5)

    return hs.getPosition()

if __name__ == "__main__":

    hs = HoistStepper(port= "COM10", calibrated = True)

    print(hoist(hs, 0.15))
    sleep(1)
    print(hoist(hs, 0))




