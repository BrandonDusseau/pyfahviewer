from .fahclientexception import FahClientException
import requests

def get_team_stats(team_num):
    uri = "https://stats.foldingathome.org/api/team/{0}".format(team_num)
    req = requests.get(uri)

    if req.status_code != 200:
        return None

    team_stats = req.json()

    return team_stats
