import berserk
import lichess.api
import fidetournament.tournament
import os

if 'LICHESS_TOKEN' in os.environ:
    lichess_token = os.environ['LICHESS_TOKEN']
    session = berserk.TokenSession(lichess_token)
    client = berserk.Client(session = session)
else:
    client = berserk.Client()

import chess.pgn
import datetime
from pytz import timezone

import argparse
import requests
import io
import dateutil.parser

def get_players(club):
    return [ m['id'] for m in client.teams.get_members(club) ]

def get_tournaments(user):
    return [ t['id'] for t in client.tournaments.stream_by_creator(user) if 'wallasey' in t['fullName'].lower() ]

def get_pgn(game):
    return client.games.export(game, as_pgn=True)

def game2dict(g, pgn=''):
    toReturn = {}
    if 'pgn' == '' and pgn in g.keys():
        pgn = g['pgn']
    result = 0
    if 'winner' in g.keys():
        if g['winner'] == 'white' : result = 1
        if g['winner'] == 'black' : result = 2
    toReturn[g['id']] = { 'white' : g['players']['white']['user']['id'], 'black' : g['players']['black']['user']['id'], 'result' : result, 'date' : g['createdAt'], 'pgn' : pgn}
    return toReturn


def get_game(game_id):
    g = client.games.export(game_id)
    pgn=''
    if 'pgn' in g.keys():
        pgn = g['pgn']
    else: 
        pgn = get_pgn(game_id)
    return game2dict(g, pgn=pgn)

def get_arena_games(tournament_id):
    games = client.tournaments.export_games(tournament_id)
    toReturn = {}
    for g in games:
        toReturn.update(game2dict(g))
    return toReturn

def get_games_from_pgn(pgn):
    game = chess.pgn.read_game(pgn)
    toReturn = {}
    while (game):
        heads = game.headers
        id = heads['Site'].replace('https://lichess.org/','')
        result = 0
        time = heads['UTCTime']
        date = heads['Date']
        format = '%Y.%m.%d %H:%M:%S'
        print(heads['Result'])
        if heads['Result'] == '1-0' : result = 1
        if heads['Result'] == '0-1' : result = 2
        toReturn[id] = {'white': heads['White'].lower(), 'black' : heads['Black'].lower(), 'result' : result, 'date' : datetime.datetime.strptime(date + ' ' + time,format), 'pgn' : game}
        game = chess.pgn.read_game(pgn)
    return toReturn

def get_swiss_games(t):
    games = {}
    pgn = requests.get('https://lichess.org/api/swiss/'+t+'/games',allow_redirects=True)
    pgn_bytes = io.BytesIO(pgn.content)
    wrapper = io.TextIOWrapper(pgn_bytes, encoding='utf-8')
    games.update(get_games_from_pgn(wrapper))
    return games
