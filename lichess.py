
import berserk
client = berserk.Client()

import chess.pgn
import datetime

import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "chessclub.settings"
django.setup()

from league.models import Player, Season, Schedule, Standings

def get_players(club):
    return [ m['id'] for m in client.teams.get_members(club) ]

def get_tournaments(user):
    return [ t['id'] for t in client.tournaments.stream_by_creator('sfarry') if 'wallasey' in t['fullName'].lower() ]

def get_pgn(game):
    return client.games.export(game, as_pgn=True)

def get_games(tournament):
    games = client.tournaments.export_games(tournament)
    toReturn = {}
    for g in games:
        result = 0
        if 'winner' in g.keys():
            if g['winner'] == 'white' : result = 1
            if g['winner'] == 'black' : result = 2
        toReturn[g['id']] = { 'white' : g['players']['white']['user']['id'], 'black' : g['players']['black']['user']['id'], 'result' : result, 'date' : g['createdAt']}
    return toReturn

def get_games_from_pgn(pgn):
    f = open(pgn)
    game = chess.pgn.read_game(f)
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
        game = chess.pgn.read_game(f)
    return toReturn

known_players = {
    'Cymbeline' : ['Mike', 'Coffey'],
    'Bish-Bash-Bosh' : ['Brian', 'Wigget'],
    'VasillySlimyslob' : ['Richard', 'Kelly'],
    'Jacko787' : ['Alan', 'Jackson'],
    'stethomas' : ['Steve', 'Thomas'],
    'RickPurcell10' : ['Rick', 'Purcell'],
    'leonwolszczak' : ['Leon', 'Wolszczak'],
    'felixfarmyardz1' : ['Felix', 'LeFeuvre'],
    'colinhugheswirral' : ['Colin', 'Hughes'],
    'ColRees' : ['Colin', 'Rees'],
    'C7essMaster' : ['Robert', 'Steele'],
    'Marty240' : ['Trevor', 'Amos']
}

# add all lower case as api returns just lower case
keys = list(known_players.keys())
for k in keys:
    known_players[k.lower()] = known_players[k]

if __name__ == "__main__":
    #let's get all our players and add them to the database
    '''
    players = get_players('wallasey-chess-club')
    for p in players:
        if len(Player.objects.filter(lichess=p)) > 0:
            print(p,' already is in the database')
        else:
            print('ned to add ',p,' to the database')
            if p in known_players.keys():
                known_player = known_players[p]
                newplayer = Player(name=known_player[0],surename=known_player[1],lichess=p)
                newplayer.save()
            else:
                newplayer = Player(name=p,lichess=p)
                newplayer.save()
            print('added')
    
    tournaments = get_tournaments('sfarry')
    '''
    tournaments = ['5QTqdT2E']
    games = {}
    #for t in tournaments:
    #    games.update(get_games(t))

    swiss = '/Users/sfarry/Downloads/lichess_swiss_2020.05.21_5QTqdT2E_wallasey-swiss.pgn'

    games.update(get_games_from_pgn(swiss))

    season = Season.objects.filter(name="Lichess Online").filter(league="Rapid 2020")[0]
    for g,v in games.items():
        white = Player.objects.filter(lichess=v['white'])
        black = Player.objects.filter(lichess=v['black'])
        schedule = Schedule(season=season,lichess=g,white=white[0],black=black[0],date=v['date'],result=v['result'])
        #schedule.pgn = get_pgn(g)
        schedule.pgn = v['pgn']
        print(schedule.white,schedule.black,"result:",schedule.result)
        schedule.save()
'''
    games = Schedule.objects.all()
    for g in games:
        if g.lichess:
            g.pgn=get_pgn(g.lichess)
            g.save()
    '''


    
