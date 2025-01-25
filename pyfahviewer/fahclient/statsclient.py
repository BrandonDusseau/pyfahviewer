import json
import requests
import time
from datetime import datetime


class StatsClient(object):
    team_stats_cache = None
    team_members_cache = None
    team_stats_expire = 0
    team_members_expire = 0

    # Fetches team statistics from the F@H server.
    def get_team_stats(self, team_num):
        if self.team_stats_cache is not None and round(time.time()) < self.team_stats_expire:
            return json.loads(self.team_stats_cache)

        uri = "https://api2.foldingathome.org/team/{0}".format(team_num)

        # Include a referer header to circumvent the API server blocking the request.
        headers = {
            'Referer': 'https://stats.foldingathome.org/'
        }
        req = requests.get(uri, headers=headers)

        if req.status_code != 200:
            return None

        team_stats = req.json()

        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        team_stats["fetch_time"] = fetch_time

        self.team_stats_cache = json.dumps(team_stats)
        self.team_stats_expire = round(time.time()) + 300

        return team_stats

    # Fetches team member statistics from the F@H server.
    def get_team_members(self, team_num):
        if self.team_members_cache is not None and round(time.time()) < self.team_members_expire:
            return json.loads(self.team_members_cache)

        uri = "https://api2.foldingathome.org/team/{0}/members".format(team_num)

        # Include a referer header to circumvent the API server blocking the request.
        headers = {
            'Referer': 'https://stats.foldingathome.org/'
        }
        req = requests.get(uri, headers=headers)

        if req.status_code != 200:
            return None

        team_members_raw = req.json()

        team_members = {
            'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'members': []
        }

        for member in team_members_raw[1:]:
            team_members['members'].append({
                'name': member[0],
                'rank': member[2],
                'score': member[3],
                'wus': member[4]
            })

        self.team_members_cache = json.dumps(team_members)
        self.team_members_expire = round(time.time()) + 300

        return team_members
