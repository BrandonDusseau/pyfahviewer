import hashlib
import json
import re
import time
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK


class V8Client(object):
    slot_stats_cache = {}
    slot_stats_expire = {}

    # Gets slot and related queue information from a Folding@Home client.
    async def get_slots_and_queues(self, server):
        server_addr = server["address"]
        server_port = server["port"]

        # Return data from cache if possible.
        if (self.slot_stats_cache.get(server_addr) is not None
            and round(time.time()) < self.slot_stats_expire.get(server_addr)):
            print("Returning cache data")
            return json.loads(self.slot_stats_cache.get(server_addr))

        print("Contacting v8 server '{0}'...".format(server_addr))

        uri = f"ws://{server_addr}:{server_port}/api/websocket"

        try:
            async with connect(uri) as websocket:
                data = json.loads(await websocket.recv())
        except ConnectionClosedOK:
            pass
        except Exception as e:
            print("Error getting data from {0}: {1}".format(uri, str(e)))
            return None

        slots = []

        server_info = data.get("info", {})
        server_name = server_info.get("mach_name", server_addr)
        gpus = server_info.get("gpus", {})
        gpu_names = {gpu_name: gpu_info.get("description", "Unknown GPU") for gpu_name, gpu_info in gpus.items()}
        work_units = data.get("units", [])
        groups = data.get("groups", [])

        devices = []

        for group_name, group_info in groups.items():
            group_config = group_info.get("config", {})

            if group_config.get("cpus", 0) > 0:
                devices.append({
                    "group": group_name,
                    "device_id": "cpu",
                    "name": "CPU",
                    "cores": group_config.get("cpus"),
                    "paused": group_config.get("paused", False),
                    "finishing": group_config.get("finish", False),
                })

            for group_gpu_id, group_gpu_state in group_config.get("gpus", {}).items():
                if group_gpu_state is None or not group_gpu_state.get("enabled", False):
                    continue

                devices.append({
                    "group": group_name,
                    "device_id": group_gpu_id,
                    "name": gpu_names[group_gpu_id],
                    "cores": None,
                    "paused": group_config.get("paused", False),
                    "finishing": group_config.get("finish", False),
                })

        for device in devices:
            active_work_unit = None

            for work_unit in work_units:
                if work_unit.get("group") != device["group"]:
                    continue

                wu_gpus = work_unit.get("gpus", [])

                if len(wu_gpus) != 0 and device["device_id"] == "cpu":
                    continue
                elif device["device_id"] != "cpu" and device["device_id"] not in work_unit.get("gpus", []):
                    continue

                active_work_unit = work_unit
                break

            has_work_unit = active_work_unit is not None

            time_remaining = self.__get_time_remaining(active_work_unit)

            slots.append({
                "server": server_name,
                "type": "cpu" if device["device_id"] == "cpu" else "gpu",
                "hash": hashlib.md5(f"{server_addr}:{device["group"]}:{device["device_id"]}".encode()).hexdigest(),
                "cores": device["cores"],
                "name": device["name"],
                "percentdone": round(active_work_unit.get("wu_progress", 0) * 100, 2) if has_work_unit else 0,
                "creditestimate": active_work_unit.get("ppd", 0) if has_work_unit else None,
                "status": self.__get_slot_status(device, active_work_unit),
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

    def __get_slot_status(self, device, work_unit):
        if work_unit is None:
            return "ready"

        if work_unit.get("state") == "DOWNLOAD":
            return "downloading"

        if work_unit.get("state") == "UPLOAD":
            return "uploading"

        if device["paused"]:
            return "paused"

        if device["finishing"]:
            return "stopping"

        return "running"

    def __get_time_remaining(self, work_unit):
        if work_unit is None:
            return (0, 0, 0, 0)

        match = re.match(r"(?:(\d+)d\s?)?(?:(\d+)h\s?)?(?:(\d+)m\s?)?(?:(\d+)s)?", work_unit.get("eta", ""))

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
