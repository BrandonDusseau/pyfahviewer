import json
import requests
import time
from .fahclientexception import FahClientException
from datetime import datetime


class StatsClient(object):
    team_stats_cache = None
    team_stats_expire = 0

    def get_team_stats(self, team_num):
        if self.team_stats_cache is not None and round(time.time()) < self.team_stats_expire:
            return json.loads(self.team_stats_cache)

        uri = "https://stats.foldingathome.org/api/team/{0}".format(team_num)
        req = requests.get(uri)

        if req.status_code != 200:
            return None

        team_stats = req.json()

        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        team_stats["fetch_time"] = fetch_time

        self.team_stats_cache = json.dumps(team_stats)
        self.team_stats_expire = round(time.time()) + 300

        return team_stats
