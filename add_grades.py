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

import csv

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
def get_players(f):
    players = requests.get('http://www.ecfgrading.org.uk/files/'+f,allow_redirects=True)
    wallasey_players = []
    bytes = io.BytesIO(players.content)
    wrapper = io.TextIOWrapper(bytes, encoding='latin')
    spamreader = csv.reader(wrapper, delimiter=',', quotechar='"')
    for row in spamreader:
        ref = row[0]
        names = row[1].split(',')
        grade = row[5]
        clubs = [row[12],row[13],row[14],row[15]]

        if 'Wallasey' in clubs:
            wallasey_players += [{
                'ecf' : ref, 'name': names[0].strip(), 'firstname': names[1].strip(), 'grade' : grade
            }]
    return wallasey_players

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Give arguments to add tournaments.')
    parser.add_argument('--file', dest='gradingfile', type=str, default = 'grades202001.csv', nargs='+',
                        help='Swiss tournaments results to add')

    args = parser.parse_args()
    print(args)
    #let's get all our players and add them to the database
    '''
    wallasey_players = get_players(args.gradingfile)
    for p in wallasey_players:
        print(p['firstname'],p['name'],p['ecf'],p['grade'])
        matches = Player.objects.filter(ecf=p['ecf'])
        if len(matches) == 0:
            print(p)
            grade = 0
            if (p['grade'] != ''): grade = int(p['grade'])
            player = Player(name=p['firstname'], surename=p['name'], ecf=p['ecf'], grade=grade)
            player.save()
            #matches[0].ecf = p['ecf']
            #matches[0].grade = p['grade']
            #matches[0].save()
            #print(matches[0],"saved")

    ''' 
    '''
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
    '''
    players = Player.objects.all()
    for p in players:
        if p.ecf == None: continue
        url = 'https://www.ecfrating.org.uk/v2/new/api.php?v2/ratings/Standard/'+str(p.ecf)+'/2020-12-22'
        print(url)
        grade = requests.get(url)
        if grade:
            grade = grade.json()
            print(grade['revised_rating'])
            p.grade = grade['revised_rating']
            p.save()
