import hashlib
import json
import re
import time
from .fahclientexception import FahClientException
from math import floor
from telnetlib import Telnet
from socket import timeout


class V7Client(object):
    slot_stats_cache = {}
    slot_stats_expire = {}

    # Gets slot and related queue information from a Folding@Home client.
    def get_slots_and_queues(self, server):
        server_addr = server["address"]
        server_pass = server["password"]

        # Return data from cache if possible.
        if (self.slot_stats_cache.get(server_addr) is not None
                and round(time.time()) < self.slot_stats_expire.get(server_addr)):
            return json.loads(self.slot_stats_cache.get(server_addr))

        print("Contacting v7 server '{0}'...".format(server_addr))

        tn = None
        try:
            tn = Telnet(server_addr, "36330", 5)

            self.__wait_for_prompt(tn)

            if server_pass:
                tn.write("auth {0}\n".format(server_pass).encode())
                self.__wait_for_auth(tn)
                self.__wait_for_prompt(tn)

            tn.write("slot-info\n".encode())
            slot_data = self.__get_data(tn, "\nPyON 1 slots\n")

            self.__wait_for_prompt(tn)
            tn.write("queue-info\n".encode())
            queue_data = self.__get_data(tn, "\nPyON 1 units\n")

            tn.close()
        except (timeout, EOFError, FahClientException, OSError) as e:
            print("Error getting data from {0}: {1}".format(server_addr, str(e)))

            if tn is not None:
                tn.close()

            return None

        client_slots = eval(slot_data, {}, {})
        queues = eval(queue_data, {}, {})

        client_slots = self.__enhance_slots(client_slots, queues, server_addr)

        slots = []
        for slot in client_slots:
            queue = slot.get("queue")
            time_remaining = self.__get_time_remaining(queue)

            slots.append({
                "server": server_addr,
                "type": slot.get("type"),
                "hash": slot.get("hash"),
                "cores": slot.get("cores"),
                "name": slot.get("name"),
                "percentdone": queue.get("percentdone", 0),
                "creditestimate": int(queue.get("creditestimate")),
                "status": slot.get("status", "unknown").lower(),
                "eta": {
                    "days": time_remaining[0],
                    "hours": time_remaining[1],
                    "minutes": time_remaining[2],
                    "seconds": time_remaining[3],
                }
            })

        self.slot_stats_cache[server_addr] = json.dumps(slots)
        self.slot_stats_expire[server_addr] = round(time.time()) + 10

        print("Finished slots for '{0}'".format(server_addr))
        return slots

    def __get_time_remaining(self, queue):
        match = re.match(
            r"(?:(\d+) days?\s?)?(?:(\d+) hours?\s?)?(?:(\d+) mins?\s?)?(?:(\d+) secs?)?",
            queue.get("eta", ""))

        if match is None:
            return (0, 0, 0, 0)

        days_str = match.group(1)
        days = 0 if days_str is None else int(days_str)

        hours_str = match.group(2)
        hours = 0 if hours_str is None else int(hours_str)

        minutes_str = match.group(3)
        minutes = 0 if minutes_str is None else int(minutes_str)

        seconds_str = match.group(4)
        seconds = 0 if seconds_str is None else int(seconds_str)

        return (days, hours, minutes, seconds)

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
                        q["percentdone"] = round(float(q["percentdone"].replace("%", "")), 2)
                        q["percentdoneclean"] = floor(float(q["percentdone"]))
                        selected_queue = q

            s["queue"] = selected_queue if selected_queue is not None else {}

            slot_info = s["description"].split(":")
            s["type"] = slot_info[0]
            if slot_info[0] == "cpu":
                s["cores"] = int(slot_info[1])
                s["name"] = "CPU"
            elif slot_info[0] == "gpu":
                match = re.match(r"^(?:[^[]*\[)?([^\]]+)\]?", slot_info[2])
                s["cores"] = None
                s["name"] = match.group(1) if match is not None else "Unknown GPU"

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
                "Unable to locate expected data header, got: {0}".format(response[2].decode()))
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
