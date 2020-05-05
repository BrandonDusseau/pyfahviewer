#!/usr/bin/python
from concurrent.futures import ThreadPoolExecutor
from .config import get_config
from .fahclient import LocalClient, StatsClient
from flask import Flask, render_template, jsonify, abort
import os

app = Flask(__name__)
stats_client = StatsClient()
local_client = LocalClient()

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

    return jsonify(stats_client.get_team_stats(team))


@app.route('/api/slots')
def get_slots():
    servers = get_config('servers')

    if servers is not None and type(servers) is not list:
        print('Configuration error: `servers` must be a list.')
        abort(500)

    if get_config('mock_slots'):
        return __get_mock('slots.json')

    if servers is None or len(servers) == 0:
        print('Returning no slot data because no servers are configured.')
        return jsonify({'disabled': True})

    with ThreadPoolExecutor(max_workers=3) as executor:
        slot_results = executor.map(local_client.get_slots_and_queues, servers)

    slots = []
    for slot_result in slot_results:
        if slot_result is not None:
            slots = slots + slot_result

    return jsonify({'slots': slots})


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
