from .fahclientexception import FahClientException
from telnetlib import Telnet
from socket import timeout
import re

def get_slots_and_queues(server, port="36330"):
    slot_pyon = None
    try:
        with Telnet(server, port, 5) as tn:
            __wait_for_prompt(tn)
            tn.write("slot-info\n".encode())
            slot_data = __get_data(tn, "\nPyON 1 slots\n")

            __wait_for_prompt(tn)
            tn.write("queue-info\n".encode())
            queue_data = __get_data(tn, "\nPyON 1 units\n")
    except (timeout, EOFError, FahClientException):
        return None

    slots = eval(slot_data, {}, {})
    queues = eval(queue_data, {}, {})
    return {"slots": slots, "queues": queues}

def __wait_for_prompt(tn):
    prompt = "> "
    prompt_wait = tn.read_until(prompt.encode(), 2)

    if prompt_wait[-len(prompt):].decode() != prompt:
        raise FahClientException("Could not read prompt from telnet connection.")

def __get_data(tn, expected_header):
    response_wait = tn.read_until(expected_header.encode(), 2)

    if response_wait[:len(expected_header)].decode() != expected_header:
        raise FahClientException(
            "Unable to locate expected data header, got: {0}".format(response_wait.decode()))

    footer = "\n---\n"
    data_bytes = tn.read_until(footer.encode(), 2)

    if data_bytes[-len(footer):].decode() != footer:
        raise FahClientException("Unable to retrieve data section from response.")

    return data_bytes[:-len(footer)].decode()
