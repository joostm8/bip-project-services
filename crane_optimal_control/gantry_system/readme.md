
gantry system: final system, uses code from various other modules in 
this project to implement 3 main scripts. Startup procedure would be 
Validator > Simulator > Controller
Perhaps good idea to also create a dummy gantry controller at first, 
makes testing it simpler.

Todo:

- (Mock) gantry controller:
    - [x] calculate trajectory, store in database
    - [x] signal simulator to simulate replications (currently done by foo)
    - [x] Execute + log trajectory -> previously I did this in two python instances for performance, should I do the same here or use multiprocessing? Seems that since logging and executing this should occur simultaneously, I guess multiprocessing is better, to keep it all in one script? Actually, multiprocessing isn't needed, just need to sample the UART when the position gets updated. I mean, can do multiprocessing if we see it's not working out, but I think it will.

    Have a look at tmc4671_printer_execute_waypoints, which has all the code needed to execute the waypoints (data conversions as well).

    Then for logging, the Printer class should be adjusted.
    Loggin functionality from angle-measurement must be added.

    - [x] Log trajectory gets written to database
    - [x] Signal validator that logged trajectory is available
    - [x] write unittests

- Simulator
    - [x] starts up, waits for signal from gantry controller that X replications of a trajectory are requested
    - [x] spawn the simulations, let them complete in the background, simulation should write their results to the database. This is partly done, that is, I can spawn the simulations, but the simulation code is still missing, this needs to be placed into some class, which should take care of solving, but also sampling of the replications.
    - [x] synchronization/keeping track of simulations then once all replications of a trajectory are wrapped up, signal the validator that this is done. Done, except the signaling is just a printout, but close enought.

- Validator
    - [x] Track trajectory ID's and wait for signal on trajectory ID of both the gantry controller and the simulator.
        - [x] Test this
    - [x] once both checked, get logs from database, resample to the same timepoints and calculate metric
    - [x] Store record of this calculation in database. What needs to be in there?  ID, name of the metric, 