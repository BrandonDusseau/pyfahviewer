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
    except (timeout, EOFError, FahClientException) as e:
        print("Error getting data from {0}: {1}".format(server, str(e)))
        return None

    slots = eval(slot_data, {}, {})
    queues = eval(queue_data, {}, {})

    for s in slots:
        selected_queue = None
        for q in queues:
            if q["slot"] != s["id"]:
                continue

            if (selected_queue is None or
                __compare_queue_status(q["state"], selected_queue["state"]) >= 0):
                q["percentdoneclean"] = round(float(q["percentdone"].replace("%", "")))
                selected_queue = q

        s["queue"] = selected_queue
        s["server"] = server

        slot_info = s["description"].split(":")
        s["type"] = slot_info[0]
        if slot_info[0] == "cpu":
            s["cores"] = slot_info[1]
            s["name"] = "CPU"
        elif slot_info[0] == "gpu":
            s["cores"] = None
            s["name"] = slot_info[2]

    return slots

def __compare_queue_status(stat1, stat2):
    priority = {
        "UPLOAD": 0,
        "DOWNLOAD": 1,
        "STOPPING": 2,
        "PAUSED": 3,
        "FINISHING": 4,
        "READY": 5
    }

    return priority.get(stat1, -1) - priority.get(stat2, -1)

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
