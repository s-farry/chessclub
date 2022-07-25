import berserk
import lichess.api
import fidetournament.tournament

lichess_token = '2LearXaxmENFzfVv'
session = berserk.TokenSession(lichess_token)
client = berserk.Client(session = session)

import chess.pgn
import datetime
from pytz import timezone

import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "chessclub.settings"
django.setup()

import argparse
import requests
import io
import dateutil.parser


from league.models import Player, Season, League, Schedule, Standings
from content.models import event, album
from league.admin import standings_update, standings_save       

from league.utils import *

players = Player.objects.all()
player_names = {p.__str__() : p  for p in players}
summer_tournament_players = {}
import pandas as pd


season = Season.objects.all()[2]

league = League(id=24, season=season, name='Summer Tournament', slug='summer-2021-2022', updated_date = datetime.datetime.now(), win_points = 1.0, draw_points = 0.5, lost_points = 0.0)

league.save()

summer_tournament_crosstable = pd.read_csv('/home/sfarry/Documents/summer tournament.csv')

for i,p in summer_tournament_crosstable.iterrows():
    if np.isnan(p['Index']): continue
    if p['Player'] not in player_names.keys():
        print('%s not in database '%(p['Player']))
    else:
        summer_tournament_players[p['Index']] = player_names[p['Player']]

for player in summer_tournament_players.values():
    league.players.add(player)

for i,p in summer_tournament_crosstable.iterrows():
    if np.isnan(p['Index']): continue
    for j in range(i,35):
        color=''
        if not np.isnan(p[str(j+1)]):
            if (i%2 == j%2 and j < i) or (i%2 != j%2 and j > i):
                color = 'white'
            else:
                color = 'black'
            '''
            if (i+1)%2 == 0 :
                if (j+1)%2 == 0 :
                    if j+1 > i + 1 : color = 'black'
                    else: color = 'white'
                else:
                    if j+1 > i + 1 : color = 'white'
                    else: color = 'black'
            else:

                if (j+1)%2 == 0 :
                    if j+1 > i + 1 : color = 'white'
                    else: color = 'black'
                else:
                    if j+1 > i + 1 : color = 'black'
                    else: color = 'white'
            '''

            result = p[str(j+1)]
            reverse_result = summer_tournament_crosstable.iloc[j][str(i+1)]


            if color == 'white':
                if result == 1 :
                    print_result = '1 - 0'
                elif result == 0 :
                    print_result = '0 - 1'
                elif result == 0.5:
                    print_result = '1/2 - 1/2'

            else:
                if result == 1 :
                    print_result = '0 - 1'
                elif result == 0 :
                    print_result = '1 - 0'
                elif result == 0.5:
                    print_result = '1/2 - 1/2'

            game = Schedule(league=league, date = datetime.datetime(month=7, day=18, year=2022, hour=19, minute=30))
            if color == 'white':
                game.white = summer_tournament_players[p['Index']]
                game.black = summer_tournament_players[j+1]

                if result == 1:
                    game.result = 1
                elif result == 0:
                    game.result = 2
                elif result == 0.5:
                    game.result = 0

            else:
                game.black = summer_tournament_players[p['Index']]
                game.white = summer_tournament_players[j+1]

                if result == 1:
                    game.result = 2
                elif result == 0:
                    game.result = 1
                elif result == 0.5:
                    game.result = 0

            game.save()

            if np.isnan(reverse_result):
                if color == 'white':
                    print( '%s %s %s' % (summer_tournament_players[p['Index']], print_result, summer_tournament_players[j+1]))
                else:
                    print( '%s %s %s' % (summer_tournament_players[j+1], print_result, summer_tournament_players[p['Index']]) )
                print("Reverse result does not exist")

            if not np.isnan(reverse_result) and ((result == 1 and reverse_result != 0) or (result == 0 and reverse_result != 1) or (result == 0.5 and reverse_result != 0.5) or (reverse_result == 0.5 and result != 0.5)) :
                if color == 'white':
                    print( '%s %s %s' % (summer_tournament_players[p['Index']], print_result, summer_tournament_players[j+1]))
                else:
                    print( '%s %s %s' % (summer_tournament_players[j+1], print_result, summer_tournament_players[p['Index']]) )
                print("Reverse result does not match %.1f %.1f"%(result, reverse_result))

