# this script connects to the meshtastic mesh via serial interface and relays the messages to cable AI.
# assumes the server is already running.
import logging
import time
import re
import sys
import signal
import meshtastic.serial_interface
from pgpt_python.client import PrivateGPTApi
from pubsub import pub

# Configure logging
logging.basicConfig(filename='logfile.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
debug = False


def log_file(log_message):
    """
    Log a message to the file.

    Args:
        log_message (str): The message to be logged.
    """
    logging.info(log_message)


def log_printout(printout):
    """
    Print a message to the console (if debug mode is enabled).

    Args:
        printout (str): The message to be printed.
    """
    if debug:
        print(printout)


def connect_to_ai():
    """
    Connect to the Cable AI server.

    Returns:
        PrivateGPTApi or None: An instance of the PrivateGPTApi if connection is successful, else None.
    """
    try:
        client = PrivateGPTApi(base_url="http://localhost:8001", timeout=180)
        if client.health.health():
            log_file('AI online')
            log_printout("--- AI online ---")
            return client
    except Exception as e:
        log_printout("Could not connect to Cable AI. Is it running? Please run './start_ai.sh' in a separate terminal."
                     f"{e}")
    return None


def load_system_prompt(file_path):
    """
    Load the system prompt from a file.

    Args:
        file_path (str): The path to the file containing the system prompt.

    Returns:
        str: The system prompt loaded from the file.
    """
    try:
        with open(file_path, 'r') as file:
            return file.read().strip().replace('\n', '').replace('\r\n', '')
    except Exception as e:
        log_printout(f"Error loading system prompt: {e}")


def send_to_mesh(msg, interface):
    """
    Send a message to the Meshtastic mesh.

    Args:
        msg (str): The message to be sent.
        interface: The interface object for communication with the mesh.
    """
    try:
        interface.sendText(msg)
    except Exception as e:
        log_printout(f"Could not send message to mesh: {e}")


def handle_packet(packet, interface, system_prompt, client):
    """
    Handle the incoming packet from the mesh.

    Args:
        packet (dict): The packet received from the mesh.
        interface: The interface object for communication with the mesh.
        system_prompt (str): The system prompt to be used for AI queries.
        client: The PrivateGPTApi client for querying the AI.
    """
    decoded = packet.get('decoded')
    if not decoded or decoded.get('portnum') != "TEXT_MESSAGE_APP":
        return

    msg = decoded.get('payload').decode('utf-8')
    send_to_mesh("Aether is processing your request.", interface)
    start_time = time.time()
    answer = query_with_context(msg, system_prompt, client, interface)
    end_time = time.time()
    send_chunks(answer, interface)
    log_file(f'--- prompt: {msg}')
    log_file(f'--- response: {answer}')
    log_file(f"---Time for query : {int(end_time - start_time)} seconds ---")


def query_with_context(msg, system_prompt, client, interface):
    """
    Query the AI with the given message and system prompt.

    Args:
        msg (str): The message to be sent to the AI.
        system_prompt (str): The system prompt to be used for AI queries.
        client: The PrivateGPTApi client for querying the AI.
        interface: The interface object for communication with the mesh.

    Returns:
        str: The AI's response to the query.
    """
    if client:
        try:
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
        except Exception as e:
            log_printout(f"Error querying AI: {e}")
            log_file(f"Error querying AI: {e}")
    else:
        log_printout("---AI offline---")
        log_file("---AI offline---")
        send_to_mesh("AI offline. Please find Aron or Joel to reboot it.", interface=interface)
    return ''


def send_chunks(answer, interface):
    """
    Send the response message in chunks to the mesh interface.

    Args:
        answer (str): The response message from the AI.
        interface: The interface object for communication with the mesh.
    """
    chunksize = 128
    sleeptime = 3
    words = re.findall(r'\S+\s*', answer)
    chunks = ['']
    for word in words:
        if len(chunks[-1]) + len(word) <= chunksize:
            chunks[-1] += word
        else:
            chunks.append(word)
    for chunk in chunks:
        send_to_mesh(chunk, interface)
        time.sleep(sleeptime)


def shutdown_gracefully(signal, frame, interface):
    """
    Gracefully shut down the script.

    Args:
        signal: The signal received to trigger the shutdown.
        frame: The frame object associated with the signal.
        interface: The interface object for communication with the mesh.
    """
    log_printout("Shutting down...")
    log_file("Shutting down...")
    if interface:
        interface.close()
    sys.exit(0)


def main():
    """
    The main function of the script.
    """
    log_printout('---starting the mesh interface---')
    log_file('---starting the mesh interface---')
    interface = meshtastic.serial_interface.SerialInterface()

    client = connect_to_ai()
    if not client:
        return

    system_prompt = load_system_prompt('/Users/aron/sdr/ai_narration/system_prompt.txt')

    pub.subscribe(handle_packet, "meshtastic.receive", interface=interface, system_prompt=system_prompt, client=client)

    signal.signal(signal.SIGINT, lambda sig, frame: shutdown_gracefully(sig, frame, interface))

    log_printout("Press 'Ctrl + c' to exit.")
    log_file("Press 'Ctrl + c' to exit.")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        send_to_mesh("Aether is going offline.", interface)

    if interface:
        interface.close()


if __name__ == "__main__":
    main()
