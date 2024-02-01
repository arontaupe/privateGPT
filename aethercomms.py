# this script connects to the meshtastic mesh via serial interface and relays the messages to cable ai. assumes the server is already running.

import meshtastic.serial_interface
from pubsub import pub
import time
from pgpt_python.client import PrivateGPTApi
import signal
import sys

print('---starting the mesh interface---')
# Make sure the AI client is running, establish a connection


try:
    client = PrivateGPTApi(base_url="http://localhost:8001", timeout=180)
    print(client.health.health())
except Exception as e:
    print("Could not connect to Cable AI. Is it running? Please run './start_ai.sh' in a separate terminal.")
    exit()

debug = True

system_prompt = ''

print(f'Load system prompt from file')

# Open the file in read mode
with open('/Users/aron/sdr/ai_narration/system_prompt.txt', 'r') as file:
    # Read the content of the file and store it in a variable
    system_prompt = file.read().strip().replace('\n', '').replace('\r\n', '')

if debug:
    print(f'{system_prompt=}')

if client.health.health():
    print("--- AI online --- ")

# called when a packet arrives
def onReceive(packet, interface):
    # extract the data from the packet
    # check whether it is an actual text message
    if packet.get('decoded') is None:
        return

    if packet.get('decoded').get('portnum') == "TEXT_MESSAGE_APP":
        print(f"---Received Message---")
        msg = packet.get('decoded').get('payload').decode('utf-8')
        if debug:
            print(f"{msg=}")
            print(f"---------")
        print(f"---Querying aether---")
        answer = query_with_context(msg, system_prompt=system_prompt)
        if debug:
            print(f"---Answer---")
            print(f"{answer}")
        chunksize = 228
        chunks = [answer[i:i + chunksize] for i in range(0, len(answer), chunksize)]
        print(f"---Sending---")
        for chunk in chunks:
            interface.sendText(chunk)
            print(f"---Sent: --- \n{chunk}")
            # wait
            time.sleep(0.1)  # ensuring that the messages arrive in correct order
        print(f"---Done. Idling.---")


def onConnection(interface, topic=pub.AUTO_TOPIC):  # called when we (re)connect to the radio
    # defaults to broadcast, specify a destination ID if you wish
    if debug:
        print(f"---Connected---")
        interface.sendText("Aether has connection to mesh")  # TODO better name?



pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")

# By default will try to find a meshtastic device
interface = meshtastic.serial_interface.SerialInterface()

def query_without_context(msg, system_prompt):
    print(client.health.health())
    if (client.health.health() == "status='ok'"):
        print("entered check for health")
    prompt_result = client.contextual_completions.prompt_completion(prompt=msg)
    return prompt_result.choices[0].message.content


def query_with_context(msg, system_prompt):
    if client.health.health():
        result = client.contextual_completions.prompt_completion(
            system_prompt=system_prompt,
            prompt=msg,
            use_context=True,
            include_sources=True, ).choices[0]
        answer = result.message.content
        if debug:
            answer += f" # Source: {result.sources[0].document.doc_metadata['file_name']}"

        return answer

    print("AI offline")
    return "AI offline. Please find Aron or Joel to reboot it."


def main():
    print("Press 'Ctrl + c' to exit.")

    # Register the signal handler for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_gracefully)

    while True:
        pass


def shutdown_gracefully(signal, frame):
    print("Shutting down...")
    interface.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
