#!/usr/bin/python
from config import get_config
from fahclient import LocalClient, StatsClient
from flask import Flask, render_template, jsonify, abort
from pprint import pprint

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

    slots = []
    for server in servers:
        server_slots = local_client.get_slots_and_queues(server)
        if server_slots is not None:
            slots = slots + server_slots

    return jsonify(slots)


if __name__ == '__main__':
    app.run()
