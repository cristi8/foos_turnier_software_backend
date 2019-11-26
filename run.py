#!/usr/bin/env python3
import hashlib
import json
import logging
import os
import time

import pystache

logger = logging.getLogger(__name__)

from pymongo import MongoClient
import cherrypy
from bs4 import BeautifulSoup

DB_CLIENT = MongoClient(os.getenv('MONGO_HOST', '127.0.0.1'), int(os.getenv('MONGO_PORT', 27017)))
DB = DB_CLIENT.foosball

ROUND_NAMES = {'Profi': '2_Pro', 'Vorrunde': '1_Qualifications', 'Amateur': '3_Semipro', 'Neuling': '4_Amator'}
SYSTEM_NAMES = {'Schweizer System': 'Swiss system', 'KO-System': 'Eliminations'}


def parse_round(xml):
    s = BeautifulSoup(xml, 'html.parser')
    round_name = ROUND_NAMES.get(s.sport.disziplin['name'], s.sport.disziplin['name'])
    round_system = SYSTEM_NAMES.get(s.sport.disziplin['system'], s.sport.disziplin['system'])

    xtop = s.find_all('meldung')
    top = [
        {
            'team': team['name'],
            'place': team['platz']
        }
        for team in xtop
    ]
    xmatches = s.find_all('spiel')
    matches = [
        {
            'team1': match['heim'],  # Home
            'team2': match['gast'],  # Guest
            'team1_score': int(match.satz['heim']),
            'team2_score': int(match.satz['gast'])
        }
        for match in xmatches
    ]
    return {
        'round': round_name,
        'system': round_system,
        'top': top,
        'matches': matches
    }


class Nested(object):
    @cherrypy.expose
    def index(self, **params):
        print(params)
        return "Welcome, Login successful\n"

    @cherrypy.expose
    def termine(self, **params):
        print(params)
        rounds_info = {
        }
        db_doc = {'ts_updated': time.time()}
        for (k, v) in params.items():
            try:
                v = v.file.read()
                try:
                    round_info = parse_round(v)
                    rounds_info[round_info['round']] = round_info
                except Exception:
                    pass
                v = v.hex()
            except Exception:
                pass
            db_doc[k] = v

        tour_id = hashlib.md5(json.dumps(rounds_info, sort_keys=True).encode()).hexdigest()

        db_doc['rounds'] = rounds_info

        DB.tours.update_one({'_id': tour_id}, {'$set': db_doc}, upsert=True)

        return "Inserted successful\n"


class HelloWorld(object):
    def __init__(self):
        self.qwqw = Nested()

    @cherrypy.expose
    def index(self):
        return "Hello"

    @cherrypy.expose
    def view(self):
        db_tours = list(DB.tours.find())
        tours = []
        for db_tour in db_tours:
            rounds = []
            for round_name in sorted(db_tour['rounds'].keys()):
                rounds.append(db_tour['rounds'][round_name])
            tours.append({
                'id': db_tour['_id'],
                'rounds': rounds
            })

        data = {'tours': tours}
        return pystache.render('''<html>
<head>
<style>
.top {
    display: inline-block;
    padding: 0px;
    margin-bottom: 10px;
    border: 1px solid black;
}

.top div {
    margin-top: 3px;
    border-bottom: 1px dotted black;
    padding: 3px;
}

.matches div div {
    margin: 4px;
    display: inline-block
}

.score {
    font-weight: bold
}

.team {

    text-align: center;
    padding: 7px;
}

.team-score0 {
    background-color: lightgray;
}

.team-score1 {
    background-color: lightgreen;
}

</style>
</head>
<body>
{{#tours}}
<h1>{{id}}</h1>

{{#rounds}}
<h2>{{round}} ({{system}})</h2>


<div class="top">
{{#top}}
<div>{{place}}. {{team}}</div>
{{/top}}
</div>

<div class="matches">
{{#matches}}
<div>
    <div class="team team-score{{team1_score}}">{{team1}}</div>
    <div class="score">{{team1_score}} - {{team2_score}}</div>
    <div class="team team-score{{team2_score}}">{{team2}}</div>
</div>
{{/matches}}
</div>


{{/rounds}}
<hr />

{{/tours}}
</body>
</html>''', data)


logging.basicConfig(level=logging.INFO)
cherrypy.server.socket_host = '0.0.0.0'
cherrypy.server.socket_port = 80

cherrypy.config.update({
    'global': {
        'environment': 'production'
    }
})
cherrypy.quickstart(HelloWorld())

