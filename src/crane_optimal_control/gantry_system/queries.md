the database queries for getting the standard deviation and avg value.

select avg(abs(value)) from trajectory "\
                        + "where machine_id = " + str(machine_id)  \
                        + " and run_id = " + str(traj_id) \
                        + " and quantity = '" + str(qty) + "';"