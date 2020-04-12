#!/usr/bin/python
from concurrent.futures import ThreadPoolExecutor
from config import get_config
from fahclient import LocalClient, StatsClient
from flask import Flask, render_template, jsonify, abort

app = Flask(__name__)
stats_client = StatsClient()
local_client = LocalClient()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/team")
def get_team():
    team = get_config("team")

    if (team is None or type(team) is not str):
        print("Configuration error: `team` must be a string and not null.")
        abort(500)

    return stats_client.get_team_stats(team)


@app.route("/api/slots")
def get_slots():
    servers = get_config("servers")

    if servers is None or type(servers) is not list:
        print("Configuration error: `servers` must be a list and not null.")
        abort(500)

    with ThreadPoolExecutor(max_workers=3) as executor:
        slot_results = executor.map(local_client.get_slots_and_queues, servers)

    slots = []
    for slot_result in slot_results:
        if slot_result is not None:
            slots = slots + slot_result

    return jsonify(slots)


if __name__ == '__main__':
    app.run()
