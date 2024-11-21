from datetime import datetime, timedelta
import psycopg
from gantry_system.trajectory_generator import TrajectoryGenerator

import yaml
import json
import paho.mqtt.client as mqtt
import pickle
import os

# Load the ID from the YAML configuration file
def load_config(config_file="config.yaml"):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config.get("machine id")

class DatabaseMQTTWrapper:
    def __init__(self, config_path='config.yaml'):
        # Load the ID from the YAML configuration file
        with open(config_path, 'r') as f:
            props = yaml.safe_load(f)
            self.id = props["machine id"]

            # connection to database
            self.dbaddr = "host="+props["database address"]\
                                    + " dbname=" + props["database name"]\
                                    + " user=" + props["database user"]\
                                    + " password=" + props["database password"]
            self.connect_to_db = props["connect to db"]
            if self.connect_to_db:
                self.dbconn = psycopg.connect(self.dbaddr)
            else:
                self.dbconn = None
        
        self.tg = TrajectoryGenerator(config_path)

        # MQTT Client setup
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the command topic
        topic = f"command/bip-server/{self.id}/req/#"
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

    def on_message(self, client, userdata, msg):
        # Parse the topic to extract the trajectory-id
        topic_parts = msg.topic.split('/')
        self.run = topic_parts[-2]
        command_action = topic_parts[-1]

        # Validate if the command is the correct one
        if command_action == "store-trajectory":
            try:
                # Deserialize the trajectory
                self.received_trajectory = pickle.loads(msg.payload)
                print(f"Received trajectory on topic: {msg.topic}")

                # store it
                self.storeTrajectory(self.received_trajectory)

                # Publish the generated trajectory to the response topic
                response_topic = f"command/bip-server/{self.id}/res/store-trajectory/200"
                client.publish(response_topic)
                print(f"Published trajectory to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}")
        if command_action == "store-measurement":
            try:
                # Deserialize the trajectory
                self.received_measurement = pickle.loads(msg.payload)
                print(f"Received measurement on topic: {msg.topic}")

                # store it
                self.storeMeasurement(self.received_measurement)

                # Publish the generated trajectory to the response topic
                response_topic = f"command/bip-server/{self.id}/res/store-measurement/200"
                client.publish(response_topic)
                print(f"Published measurement to topic: {response_topic}")
            except Exception as e:
                print(f"Error processing message: {e}")               

    def start(self):
        # Start the MQTT loop to listen for messages
        self.client.loop_forever()


    def storeMeasurement(self, measurement):
        """
        Note: name of functions is chose to match the names of the
        tables in the database.

        measurement is assumed to be a tuple as returned by
        executeTrajectory
        format: (ts, x, v, a, theta, omega)
        ts : timestamps [datetime format]
        x : position [m]
        v : velocity [m/s]
        a : acceleration [m/s2]
        theta : angular position [rad]
        omega : angular velocity [rad/s]
        """
        # returned t needs to be in datetime format for writing to database
        t0_datetime = datetime.min
        t = [t0_datetime + timedelta(seconds=ts) for ts in measurement[0]]

        with self.dbconn.cursor() as cur:
            # insert the data into measurement
            with cur.copy("COPY measurement (ts, machine_id, run_id, quantity,\
                           value) FROM stdin") as copy:
                # write all quantities
                quantities = ['position', 'velocity', 'acceleration', 'angular position',\
                              'angular velocity']
                for idx, qty in enumerate(quantities, 1):
                    for (ts, data) in zip(t, measurement[idx]):
                        copy.write_row((ts, self.id, self.run, qty, data))
        # commit to database
        self.dbconn.commit()

    def storeTrajectory(self, traj):
        """
        traj is assumed to be tuple as returned by generateTrajectory
        format: (ts, xs, dxs, ddxs, thetas, dthetas, ddthetas)
        ts      : sample times of solution  [s]
        xs      : positions of solution     [m]
        dxs     : velocity of solution      [m/s]
        ddxs    : acceleration of solution  [m/s^2]
        thetas  : angular position of solution  [rad]
        dthetas : angular velocity of solution  [rad/s]
        ddthetas: angular acceleration of solution  [rad/s^2]
        us      : input force acting on cart [N]
        """
        pass 
        # replace with pub to
        # command/bip-server/crane-1/req/db-write/store-trajectory
        if self.dbconn:
            # the datetime stamps in the database require at least a year,
            # month and day, given that it's required, I might as well
            # store the trace with an offset from now, then you know
            # when it was generated.
            curr_time = datetime.min
            ts = [curr_time + timedelta(seconds=ts) for ts in traj[0]]
            with self.dbconn.cursor() as cur:
                # create the run
                cur.execute("INSERT INTO \
                            run (run_id, machine_id, starttime) \
                            VALUES (%s, %s, %s)",
                            (self.run, self.id, datetime.now()))
                # insert the data into trajectory
                with cur.copy("COPY trajectory (ts, machine_id, run_id, quantity,\
                            value) FROM stdin") as copy:
                    # write all quantities
                    quantities = ['position', 'velocity', 'acceleration',\
                                'angular position', 'angular velocity',\
                                    'angular acceleration', 'force']
                    for idx, qty in enumerate(quantities, 1):
                        for (t, data) in zip(ts, traj[idx]):
                            copy.write_row((t, self.id, self.run, qty, data))
            # commit to database
            self.dbconn.commit()

if __name__ == "__main__":
    wrapper = DatabaseMQTTWrapper(config_path="./gantry_system/crane-properties.yaml")
    wrapper.start()