import hashlib
import json
import re
import time
from .fahclientexception import FahClientException
from datetime import datetime
from telnetlib import Telnet
from socket import timeout


class LocalClient(object):
    slot_stats_cache = {}
    slot_stats_expire = {}

    def get_slots_and_queues(self, server, port="36330"):
        if self.slot_stats_cache.get(server) is not None and round(time.time()) < self.slot_stats_expire.get(server):
            return json.loads(self.slot_stats_cache.get(server))

        slot_pyon = None
        try:
            with Telnet(server, port, 5) as tn:
                self.__wait_for_prompt(tn)
                tn.write("slot-info\n".encode())
                slot_data = self.__get_data(tn, "\nPyON 1 slots\n")

                self.__wait_for_prompt(tn)
                tn.write("queue-info\n".encode())
                queue_data = self.__get_data(tn, "\nPyON 1 units\n")
        except (timeout, EOFError, FahClientException) as e:
            print("Error getting data from {0}: {1}".format(server, str(e)))
            return None

        slots = eval(slot_data, {}, {})
        queues = eval(queue_data, {}, {})

        if slots is None:
            return None

        for s in slots:
            selected_queue = None
            s["server"] = server
            s["hash"] = hashlib.md5("{0}:{1}".format(server, s["id"]).encode()).hexdigest()

            if queues is not None:
                for q in queues:
                    if q is None or q["slot"] != s["id"]:
                        continue

                    if (selected_queue is None
                        or self.__compare_queue_status(q["state"], selected_queue["state"]) >= 0):
                        q["percentdoneclean"] = round(float(q["percentdone"].replace("%", "")))
                        selected_queue = q

            s["queue"] = selected_queue

            slot_info = s["description"].split(":")
            s["type"] = slot_info[0]
            if slot_info[0] == "cpu":
                s["cores"] = slot_info[1]
                s["name"] = "CPU"
            elif slot_info[0] == "gpu":
                s["cores"] = None
                s["name"] = slot_info[2]

        self.slot_stats_cache[server] = json.dumps(slots)
        self.slot_stats_expire[server] = round(time.time()) + 5

        return slots

    def __compare_queue_status(self, stat1, stat2):
        priority = {
            "UPLOAD": 0,
            "DOWNLOAD": 1,
            "STOPPING": 2,
            "PAUSED": 3,
            "FINISHING": 4,
            "READY": 5
        }

        return priority.get(stat1, -1) - priority.get(stat2, -1)

    def __wait_for_prompt(self, tn):
        prompt = "> "
        prompt_wait = tn.read_until(prompt.encode(), 2)

        if prompt_wait[-len(prompt):].decode() != prompt:
            raise FahClientException("Could not read prompt from telnet connection.")

    def __get_data(self, tn, expected_header):
        response_wait = tn.read_until(expected_header.encode(), 2)

        if response_wait[:len(expected_header)].decode() != expected_header:
            raise FahClientException(
                "Unable to locate expected data header, got: {0}".format(response_wait.decode()))

        footer = "\n---\n"
        data_bytes = tn.read_until(footer.encode(), 2)

        if data_bytes[-len(footer):].decode() != footer:
            raise FahClientException("Unable to retrieve data section from response.")

        return data_bytes[:-len(footer)].decode()
