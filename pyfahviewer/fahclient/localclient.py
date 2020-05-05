import hashlib
import json
import re
import time
from .fahclientexception import FahClientException
from datetime import datetime
from math import floor
from telnetlib import Telnet
from socket import timeout


class LocalClient(object):
    slot_stats_cache = {}
    slot_stats_expire = {}

    # Gets slot and related queue information from a Folding@Home client.
    def get_slots_and_queues(self, server, port="36330"):
        # Backwards-compatibility: existing configs may simply have a string address.
        if type(server) is str:
            addr = server
            password = None
        elif type(server) is dict:
            addr = server.get("address")
            password = server.get("password")
            if password == "":
                password = None
        else:
            raise FahClientException("Invalid server configuration. Server list entry must be a string or dictionary.")

        # Return data from cache if possible.
        if self.slot_stats_cache.get(addr) is not None and round(time.time()) < self.slot_stats_expire.get(addr):
            return json.loads(self.slot_stats_cache.get(addr))

        print("Contacting server '{0}'...".format(addr))

        slot_pyon = None
        tn = None
        try:
            tn = Telnet(addr, port, 5)

            self.__wait_for_prompt(tn)

            if password:
                tn.write("auth {0}\n".format(password).encode())
                self.__wait_for_auth(tn)
                self.__wait_for_prompt(tn)

            tn.write("slot-info\n".encode())
            slot_data = self.__get_data(tn, "\nPyON 1 slots\n")

            self.__wait_for_prompt(tn)
            tn.write("queue-info\n".encode())
            queue_data = self.__get_data(tn, "\nPyON 1 units\n")

            tn.close()
        except (timeout, EOFError, FahClientException, OSError) as e:
            print("Error getting data from {0}: {1}".format(addr, str(e)))

            if tn is not None:
                tn.close()

            return None

        slots = eval(slot_data, {}, {})
        queues = eval(queue_data, {}, {})

        slots = self.__enhance_slots(slots, queues, addr)

        self.slot_stats_cache[addr] = json.dumps(slots)
        self.slot_stats_expire[addr] = round(time.time()) + 5

        print("Finished slots for '{0}'".format(addr))
        return slots

    # Manipulates the slot data to add clean values and inject the queue data.
    def __enhance_slots(self, slot_data, queue_data, server_addr):
        if slot_data is None:
            return None

        for s in slot_data:
            selected_queue = None
            s["server"] = server_addr
            s["hash"] = hashlib.md5("{0}:{1}".format(server_addr, s["id"]).encode()).hexdigest()

            if queue_data is not None:
                for q in queue_data:
                    if q is None or q["slot"] != s["id"]:
                        continue

                    if (selected_queue is None
                        or self.__compare_queue_status(q["state"], selected_queue["state"]) >= 0):
                        q["percentdoneclean"] = floor(float(q["percentdone"].replace("%", "")))
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

        return slot_data

    # Compares two queue entries. Returns a positive integer if stat1 has a status with a higher precedence than stat2.
    # Returns a negative number (stat2 > stat1) or zero (equal) otherwise.
    def __compare_queue_status(self, stat1, stat2):
        precedence = {
            "UPLOADING": 0,
            "DOWNLOADING": 1,
            "READY": 2,
            "STOPPING": 3,
            "PAUSED": 4,
            "FINISHING": 5,
            "RUNNING": 6
        }

        return precedence.get(stat1, -1) - precedence.get(stat2, -1)

    # Reads the telnet stream until a F@H command prompt appears.
    def __wait_for_prompt(self, tn):
        prompt = "> "
        prompt_wait = tn.read_until(prompt.encode(), 2)

        if prompt_wait[-len(prompt):].decode() != prompt:
            raise FahClientException("Could not read prompt from telnet connection.")

    # Reads the telnet stream until a F@H auth response appears.
    def __wait_for_auth(self, tn):
        auth_expectation = ["OK\n".encode(), "\nPyON 1 error\n".encode()]
        auth_result = tn.expect(auth_expectation, 3)

        if auth_result[0] == -1 or auth_result[0] == 1:
            raise FahClientException("Unable to authenticate with server. Check that the password is correct.")

    # Reads data from the telnet stream after a command is sent.
    def __get_data(self, tn, expected_header):
        expect_list = [expected_header.encode(), "unknown command".encode()]
        response = tn.expect(expect_list, 2)

        if response[0] == -1:
            # No match to our patterns.
            raise FahClientException(
                "Unable to locate expected data header, got: {0}".format(response_wait.decode()))
        elif response[0] == 1:
            # If a F@H server has password enabled and we have not authenticated, the server will return
            # "unknown command".
            raise FahClientException(
                "Unknown command error received. The server may be protected by a password or may be an "
                + "unsupported version.")

        footer = "\n---\n"
        data_bytes = tn.read_until(footer.encode(), 2)

        if data_bytes[-len(footer):].decode() != footer:
            raise FahClientException("Unable to retrieve data section from response.")

        return data_bytes[:-len(footer)].decode()
