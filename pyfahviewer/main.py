#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor
from .config import get_config
from .fahclient import V7Client, V8Client, StatsClient
from flask import Flask, render_template, jsonify, abort
import asyncio
import os

app = Flask(__name__)
stats_client = StatsClient()
v7_client = V7Client()
v8_client = V8Client()

# Dictionary to cache mock files if used, so that we don't do a ton of I/O.
mocks_cache = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/team')
def get_team():
    team = get_config('team')

    if get_config('mock_team'):
        return __get_mock('team.json')

    if (team is None or type(team) is not str):
        print('Returning no team data because a team number is not configured.')
        return {'disabled': True}

    team_stats = stats_client.get_team_stats(team)
    team_members = stats_client.get_team_members(team)

    return jsonify({'team': team_stats, 'members': team_members['members']})


@app.route('/api/slots')
def get_slots():
    configured_servers = get_config('servers')

    if configured_servers is not None and type(configured_servers) is not list:
        print('Configuration error: `servers` must be a list.')
        abort(500)

    if get_config('mock_slots'):
        return __get_mock('slots.json')

    if configured_servers is None or len(configured_servers) == 0:
        print('Returning no slot data because no servers are configured.')
        return jsonify({'disabled': True})

    servers = []
    seen_hosts = set()
    for server in configured_servers:
        host = server.get("address")
        password = server.get("password")
        port = server.get("port", "7396")
        client_version = server.get("clientVersion")

        if host is None or host == "":
            print('Configuration error: a server is missing the `address` property')
            abort(500)

        if password == "":
            password = None

        if host in seen_hosts:
            print(f'Configuration error: server {host} is configured multiple times')
            abort(500)
        seen_hosts.add(host)

        if str(client_version) == "8":
            servers.append({
                "address": host,
                "port": port,
                "isV8": True
            })
        else:
            servers.append({
                "address": host,
                "password": password,
                "isV8": False
            })

    with ThreadPoolExecutor(max_workers=3) as executor:
        slot_results = executor.map(__get_slot_data, servers)

    slots = []
    for slot_result in slot_results:
        if slot_result is not None:
            slots = slots + slot_result

    return jsonify({'slots': slots})


def __get_slot_data(server):
    if server["isV8"]:
        # The websockets implementation requires asyncio, but we can't run async code in ThreadPoolExecutor.
        # Instead, run this synchronously.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        v8_coroutine = v8_client.get_slots_and_queues(server)
        return loop.run_until_complete(v8_coroutine)
    return v7_client.get_slots_and_queues(server)


# Returns mock data from a file in the mocks/ directory.
def __get_mock(filename):
    global mocks_cache
    if mocks_cache.get(filename):
        return mocks_cache[filename]

    mock_path = os.path.join(os.path.dirname(__file__), 'mocks', filename)
    try:
        with open(mock_path, "r") as mock_file:
            data = mock_file.read()
            mocks_cache[filename] = data
            return data
    except FileNotFoundError:
        print('Mock file "{0}" was not found! Returning an error.'.format(filename))
        abort(500)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
