#!/usr/bin/python
from fahclient import LocalClient, StatsClient
from flask import Flask, render_template, jsonify
from pprint import pprint

app = Flask(__name__)
stats_client = StatsClient()
local_client = LocalClient()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/team")
def get_team():
    return stats_client.get_team_stats("236749")

@app.route("/api/slots")
def get_slots():
    servers = ["192.168.1.5", "192.168.1.246"]
    slots = []
    for server in servers:
        server_slots = local_client.get_slots_and_queues(server)
        if server_slots is not None:
            slots = slots + server_slots

    return jsonify(slots)

if __name__ == '__main__':
    app.run()
