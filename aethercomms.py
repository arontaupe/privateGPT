# this script connects to the meshtastic mesh via serial interface and relays the messages to cable ai. assumes the server is already running.

import logging
import meshtastic.serial_interface
from pubsub import pub
import time
from pgpt_python.client import PrivateGPTApi
import signal
import sys
import re

# Configure logging
logging.basicConfig(filename='logfile.log', 
level=logging.INFO, 
format='%(asctime)s - %(levelname)s - %(message)s')

debug = True

# Function to log messages
def log(log_message=None, printout=None):
    if log_message:
        logging.info(log_message)
    
    if debug and printout:
        print(printout)

log(printout='---starting the mesh interface---')
# Make sure the AI client is running, establish a connection

# By default will try to find a meshtastic device
interface = meshtastic.serial_interface.SerialInterface()

try:
    log(printout='---connecting to the AI---')
    client = PrivateGPTApi(base_url="http://localhost:8001", timeout=180)
    log(printout=f'--- Health: {client.health.health()} ---')
except Exception as e:
    log(printout="Could not connect to Cable AI. Is it running? Please run './start_ai.sh' in a separate terminal.")
    exit()

if client.health.health():
    log(log_message='AI online', 
    printout="--- AI online ---")

system_prompt = ''

log(printout=f'---Load system prompt from file---')

# Open the file in read mode
with open('/Users/aron/sdr/ai_narration/system_prompt.txt', 'r') as file:
    # Read the content of the file and store it in a variable
    system_prompt = file.read().strip().replace('\n', '').replace('\r\n', '')

if debug:
    log(printout=f'{system_prompt=}', 
    log_message=f'{system_prompt=}')


# called when a packet arrives
def onReceive(packet, interface):
    # extract the data from the packet
    # check whether it is an actual text message
    if packet.get('decoded') is None:
        return
    handle_Packet(packet, interface)


def onConnection(interface, topic=pub.AUTO_TOPIC):  # called when we (re)connect to the radio
    # defaults to broadcast, specify a destination ID if you wish
    if debug:
        log(printout=f"---Connected to mesh---")
        interface.sendText("Aether has connection to mesh")  # TODO better name?


pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")


def send_to_mesh(msg, interface=interface):
    try:
        interface.sendText(msg, 
        #wantAck=True
        )
    except Exception as e:
        log(printout=f"Could not send message to mesh: {e}", log_message=f"Could not send message to mesh: {e}")
        return
    log(f"---Sent: --- \n{msg}")


def handle_Packet(packet, interface):
    if packet.get('decoded').get('portnum') == "TEXT_MESSAGE_APP":
        log(f"---Received Message---")
        msg = packet.get('decoded').get('payload').decode('utf-8')
        if debug:
            log(f"{msg=}")
            log(f"---------")
        send_to_mesh("Aether is processing your request.", interface=interface)
        log(f"---Querying aether---")
        start_time = time.time()
        answer = query_with_context(msg, system_prompt=system_prompt)
        end_time = time.time()
        if debug:
            log(f"---Answer---")
            log(f"{answer=}")
            log(f"---Time for query : {int(end_time - start_time)} seconds ---")
        # Add a small delay before starting to send chunks
        time.sleep(1)

        chunksize = 150  # 228 is the maximum length of a message, but then it mostly fails. 160 works, but still looses occasional messages. 120 worked well.
        words = re.findall(r'\S+\s*', answer)  # Split the answer into words

        chunks = []
        current_chunk = ''

        for word in words:
            if len(current_chunk) + len(word) <= chunksize:
                current_chunk += word
            else:
                chunks.append(current_chunk)
                current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)
            
        log(f"---Sending---")
        for chunk in chunks:
            if debug:
                log(f"{chunk=}")
            send_to_mesh(chunk)
            time.sleep(3)  # wait, ensuring that the messages arrive in correct order
        log(f"---Done. Idling.---")

def query_with_context(msg, system_prompt):
    if client.health.health():
        result = client.contextual_completions.prompt_completion(
            system_prompt=system_prompt,
            prompt=msg,
            use_context=True,
            include_sources=True,
            ).choices[0]
        answer = result.message.content
        if debug:
            answer += f" # Source: {result.sources[0].document.doc_metadata['file_name']}"

        return answer

    log("---AI offline---")
    send_to_mesh("AI offline. Please find Aron or Joel to reboot it.")
    return 



def shutdown_gracefully(signal, frame):
    log("Shutting down...")
    interface.close()
    sys.exit(0)



log("Press 'Ctrl + c' to exit.")

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, shutdown_gracefully)

try:
    while True:
        pass
except KeyboardInterrupt:
    send_to_mesh("Aether is going offline.")
    pass  # Catch KeyboardInterrupt to gracefully exit the loop on Ctrl+C

# Close the serial interface after the loop
interface.close()
