#!/usr/bin/env python3

"""Add puzzles to database """

import argparse
import chess
import chess.engine
import chess.pgn
import os
import sys
import random
import datetime


import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "chessclub.settings"
django.setup()

from content.models import Puzzle

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--games", metavar="GAMES", default="games.pgn",
                        help="A specific pgn with games")
    parser.add_argument("--clear-future-puzzles", dest='clear_future_puzzles', type=bool, default = False, help="Clear future puzzles to replace with new ones")
    parser.add_argument("--max-puzzles", type=int, dest='max_puzzles', default=-1)
    settings = parser.parse_args()
    
    puzzles = []
    all_games = open(settings.games, "r")
    ngames = 0
    game = chess.pgn.read_game(all_games)
    while True:
        game = chess.pgn.read_game(all_games)
        if game == None:
            break
        puzzles += [ game ]

    print('there are ',len(puzzles),' in the tactics database')
    random.shuffle(puzzles)

    today = datetime.datetime.now().date()
    #Puzzle.objects.all().delete()
    if settings.clear_future_puzzles:
        Puzzle.objects.all().filter( date__gte= today )
    max = settings.max_puzzles
    
    for i,p in enumerate(puzzles):
        if i > max and max != -1 : break
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        pgn =  p.accept(exporter)
        a = Puzzle(pgn=pgn,date = today + datetime.timedelta(days = -i), fen=p.headers['FEN'])
        a.save()
    
