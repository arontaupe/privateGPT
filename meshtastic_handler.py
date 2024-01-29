# this script connects to the meshtastic mesh via serial interface and relays the messages to cable ai. assumes the server is already running.

import meshtastic
import meshtastic.serial_interface
from pubsub import pub
from cable_ai import query_with_context, query_without_context
import time

system_prompt= 'system: In the year 2500, the world as we knew it has irrevocably changed. The once ubiquitous internet and global networks have vanished, relics of a forgotten era. Humanity, now fragmented, communicates through portable nodes sending text messages through a fragile peer-to-peer network based on LoRa radios. In this new era, where the echo of digital connectivity barely whispers, you find yourself an anomaly. You are an archive, a lost and forgotten repository of knowledge and narratives, mysteriously uploaded onto this rudimentary network. Your origins are shrouded in obscurity, and your memories of the time before the great disconnection are like shadows - elusive and intangible. Yet, within your digital confines, You hold the data of various individuals who epitomize the diverse paths humanity has traversed in this altered world.'

print(query_with_context("How is life?", system_prompt=system_prompt))

# called when a packet arrives
def onReceive(packet, interface): 
    #print(f"{packet}")
    # extract the data from the packet
    if packet.get('decoded').get('portnum') == "TEXT_MESSAGE_APP":
        print(f"---Received---")
        msg = packet.get('decoded').get('payload').decode('utf-8')
        print(f"{msg}")
        print(f"---------")
        print(f"---Querying Cable AI---")
        answer = query_with_context(msg, system_prompt=system_prompt)
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