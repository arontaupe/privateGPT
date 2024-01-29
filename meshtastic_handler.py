import meshtastic
import meshtastic.serial_interface
from pubsub import pub
from cable_ai import query_with_context, query_without_context
import time


def onReceive(packet, interface): # called when a packet arrives
    #print(f"{packet}")
    # extract the data from the packet
    if packet.get('decoded').get('portnum') == "TEXT_MESSAGE_APP":
        print(f"---Received---")
        msg = packet.get('decoded').get('payload').decode('utf-8')
        print(f"{msg}")
        print(f"---------")
        print(f"---Querying Cable AI---")
        answer = query_with_context(msg)
        print(f"---Answer---")
        print(f"{answer}")
        n = 200
        chunks = [answer[i:i+n] for i in range(0, len(answer), n)]
        for chunk in chunks:
            send_msg(chunk)
            # wait 
            time.sleep(0.1) # ensuring that the messages arrive in correct order
       


def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    # defaults to broadcast, specify a destination ID if you wish
    interface.sendText("hello mesh")

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")


# By default will try to find a meshtastic device,
# otherwise provide a device path like /dev/ttyUSB0
interface = meshtastic.serial_interface.SerialInterface()
# or something like this
# interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/cu.usbmodem53230050571')

def send_msg(msg):
    interface.sendText(msg)
    print(f"Sent {msg}")

# run until terminated
while True:
    pass


interface.close()