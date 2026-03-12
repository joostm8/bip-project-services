import time
import random

import paho.mqtt.client as mqtt

# adapted from https://docs.emqx.com/en/cloud/latest/connect_to_deployments/python_sdk.html
# Paho MQTT is using newer API now, see https://github.com/eclipse-paho/paho.mqtt.python/blob/master/docs/migrations.rst

CRANE_TOPICS = (
    "bip/mqtt-lab/crane-0/hoist/x-pos",
    "bip/mqtt-lab/crane-0/hoist/y-pos",
    "bip/mqtt-lab/crane-0/cart/x-pos",
    "bip/mqtt-lab/crane-0/cart/y-pos",
    "bip/mqtt-lab/crane-1/hoist/x-pos",
    "bip/mqtt-lab/crane-1/hoist/y-pos",
    "bip/mqtt-lab/crane-1/cart/x-pos",
    "bip/mqtt-lab/crane-1/cart/y-pos",
)

def connect_mqtt(hostname, username, password, port=8883) -> None:
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        if reason_code > 0:
            print("Failed to connect, return code %s\n", reason_code)

    def on_disconnect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Succesfully disconnected")
        if reason_code > 0:
            print("Disconnect unsuccessful, return code %s\n", reason_code)
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set(ca_certs='./emqxsl-ca.crt')
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(hostname, port)
    return client
    
def publish(client, qos=0):
    for topic in CRANE_TOPICS:
        msg = str(random.randint(0, 100))
        msg_info = client.publish(topic, msg, qos)
        try:
            msg_info.wait_for_publish() # only works for QoS 1 and 2!
        except Exception as e:
            print(f"Exception: {e}")
        print(f"Message '{msg}' published on topic '{topic}'")


def publish_crane_position(hostname, username, password, port=8883):
    client = connect_mqtt(hostname, username, password, port)
    client.loop_start()
    # wait for client is connected
    timeout = 10
    wait_time = 0
    while not client.is_connected():
        time.sleep(0.1)
        wait_time += 0.1
        if wait_time > timeout:
            print("Client not connected within timeout")
            raise TimeoutError

    publish(client, qos=2)
    client.disconnect()

def publish_crane_position_nb():
    # publish with parameters automatically filled in
    # in future might want to create a new user for this
    publish_crane_position(
        hostname='ed1fe6fe.ala.eu-central-1.emqxsl.com',
        username='joost-mertens',
        password='bip-mqtt-lab-2026'
    )


def publish_crane_positions(hostname, username, password, port=8883, client_id=None):
    publish_crane_position(hostname, username, password, port, client_id)

if __name__ == "__main__":
    publish_crane_position(
        hostname='ed1fe6fe.ala.eu-central-1.emqxsl.com',
        username='joost-mertens',
        password='bip-mqtt-lab-2026'
    )