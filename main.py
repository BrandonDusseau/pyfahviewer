#!/usr/bin/python
from fahclient import get_slots_and_queues, get_team_stats
from pprint import pprint

pprint(get_slots_and_queues("192.168.1.5"))
pprint(get_team_stats("236749"))
