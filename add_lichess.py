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
from content.models import event
from league.admin import standings_update, standings_save       


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

def add_arena_event(e):
    tournament    = lichess.api.tournament(e)
    event_date    = dateutil.parser.parse(tournament['startsAt'])
    lichess_event = event(title=tournament['fullName'],date=event_date.replace(tzinfo=timezone('Europe/London')),link='https://lichess.org/tournament/'+e, location='Lichess Online')
    lichess_event.save()

def add_swiss_event(e):
    tournament_trf = requests.get('https://lichess.org/swiss/'+e+'.trf' ,allow_redirects=True)
    wrapper = io.TextIOWrapper(io.BytesIO(tournament_trf.content), encoding='utf-8')
    tournament = fidetournament.tournament.Tournament()
    tournament.parse(wrapper)
    event_name = tournament.name
    event_date = datetime.datetime.strptime(tournament.startdate, '%b %d, %Y')
    event_date = event_date.replace(hour=19,minute=30, tzinfo=timezone('Europe/London'))
    lichess_event = event(title=event_name,date=event_date,link='https://lichess.org/swiss/'+e, location='Lichess Online')
    lichess_event.save()

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
    'Marty240' : ['Trevor', 'Amos'],
    'hagbard1969' : ['Martin', 'Cockerill']
}

# add all lower case as api returns just lower case
keys = list(known_players.keys())
for k in keys:
    known_players[k.lower()] = known_players[k]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Give arguments to add tournaments.')
    parser.add_argument('--swiss', dest='swiss', type=str, default = [], nargs='+',
                        help='Swiss tournaments results to add')
    parser.add_argument('--arena', dest='arenas', default = [], nargs = '+', type=str, help='Arena tournament results to add')
    parser.add_argument('--league', dest='league', type=str, default='Lichess Blitz')
    parser.add_argument('--season', dest='season', type=str, default='2019/2020')
    parser.add_argument('--arena_events', nargs = '+', dest='arena_events', type=str, help = 'Upcoming Arena Events to Add', default = [])
    parser.add_argument('--swiss_events', nargs = '+', dest='swiss_events', type=str, help = 'Upcoming Swiss Events to Add', default = [])
    parser.add_argument('--create_arena_dates', nargs='+', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), dest='arena_dates', help='Dates to Create Arena Event, e.g. 2020-03-20', default =[])

    args = parser.parse_args()
    print(args)
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
    
    #tournaments = get_tournaments('sfarry')
    '''
    tournaments = []
    games = {}
    for t in args.arenas:
        games.update(get_games(t))

    for t in args.swiss:
        print(t)
        pgn = requests.get('https://lichess.org/api/swiss/'+t+'/games',allow_redirects=True)
        pgn_bytes = io.BytesIO(pgn.content)
        wrapper = io.TextIOWrapper(pgn_bytes, encoding='utf-8')
        games.update(get_games_from_pgn(wrapper))

    season = Season.objects.filter(name=args.season)[0]
    league = League.objects.filter(season=season).filter(name=args.league)[0]
    for g,v in games.items():
        if len(Schedule.objects.filter(lichess=g)) > 0:
            schedule = Schedule.objects.filter(lichess=g)[0]
            print('game already in database')
            if schedule.league != league:
                print('updating league')
                schedule.league = league
                schedule.save()
            continue
        white = Player.objects.filter(lichess=v['white'])
        black = Player.objects.filter(lichess=v['black'])
        schedule = Schedule(league=league,lichess=g,white=white[0],black=black[0],date=v['date'],result=v['result'])
        if 'pgn' in v.keys():
            schedule.pgn = v['pgn']
        else:
            schedule.pgn = get_pgn(g)
        print(schedule.white,schedule.black,"result:",schedule.result)
        schedule.save()
    if len(games.items()) > 0 :
        standings_save(league)
        standings_update(league)

    for e in args.arena_events:
        add_arena_event(e)

    for e in args.swiss_events:
        add_swiss_event(e)


    for d in args.arena_dates:
        epoch = datetime.datetime(1970, 1, 1, tzinfo = timezone('UTC'))
        date = d.replace(hour=18,minute=30, second=22, tzinfo=timezone('UTC'))
        timestamp = int((date -epoch).total_seconds())*1000

        test = client.tournaments.create(5, 3, 90, name='Wallasey Monday',
               berserkable=True, rated=True, start_date=timestamp, conditions={ 'teamMember' : {'teamId' : 'wallasey-chess-club'}})

'''
    games = Schedule.objects.all()
    for g in games:
        if g.lichess:
            g.pgn=get_pgn(g.lichess)
            g.save()
'''


    
