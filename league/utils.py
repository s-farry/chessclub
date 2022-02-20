import berserk
import lichess.api
import fidetournament.tournament
import os


import chess.pgn
import datetime
from pytz import timezone

import argparse
import requests
import io
import dateutil.parser
from django.db.models import Q


import numpy as np
# for creating online tournaments

def get_client():
    if 'LICHESS_TOKEN' in os.environ:
        lichess_token = os.environ['LICHESS_TOKEN']
        session = berserk.TokenSession(lichess_token)
        client = berserk.Client(session = session)
    else:
        client = berserk.Client()
    return client

def get_players(club):
    client = get_client()
    return [ m['id'] for m in client.teams.get_members(club) ]
    del(client)

def get_tournaments(user):
    client = get_client()
    return [ t['id'] for t in client.tournaments.stream_by_creator(user) if 'wallasey' in t['fullName'].lower() ]
    del(client)

def get_pgn(game):
    client = get_client()
    return client.games.export(game, as_pgn=True)
    del(client)

def game2dict(g, pgn=''):
    if pgn == '' and pgn in g.keys():
        pgn = g['pgn']
    result = 0
    if 'winner' in g.keys():
        if g['winner'] == 'white' : result = 1
        if g['winner'] == 'black' : result = 2
    toReturn = { 'white' : g['players']['white']['user']['id'], 'black' : g['players']['black']['user']['id'], 'result' : result, 'date' : g['createdAt'], 'pgn' : pgn}
    return toReturn


def get_game(game_id):
    client = get_client()
    g = client.games.export(game_id)
    pgn=''
    if 'pgn' in g.keys():
        pgn = g['pgn']
    else: 
        pgn = get_pgn(game_id)
    del(client)
    return game2dict(g, pgn=pgn)

def get_arena_games(tournament_id):
    client = get_client()
    games = client.tournaments.export_games(tournament_id)
    toReturn = {}
    for g in games:
        toReturn.update({g['id'] : game2dict(g)})
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

def create_arena_event(name, d, time=5, increment=3, duration=90):
    client = get_client()
    epoch = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo = timezone('UTC'))
    date = d.replace(tzinfo = timezone('Europe/London'))
    date = date.replace(hour=19,minute=30, second=0)
    timestamp = int((date -epoch).total_seconds())*1000

    tournament = client.tournaments.create(time, increment, duration, name=name,
            berserkable=True, rated=True, start_date=timestamp, conditions={ 'teamMember' : {'teamId' : 'wallasey-chess-club'}})
    del(client)
    return tournament

from .models import League, Schedule, Standings, Player, Season, STANDINGS_ORDER, POINTS

def get_performance_score(player, tournament):
    white_games = Schedule.objects.filter(white=player, league = tournament.pk)
    black_games = Schedule.objects.filter(black=player, league = tournament.pk)
    performance, n = 0.0, 0
    for g in white_games:
        if g.black and g.black.rating != None and g.black.rating > 0:
            n+=1
            performance += g.black.rating
            if g.result == 1: performance += 400
            elif g.result == 2 : performance -= 400
    for g in black_games:
        if g.white and g.white.rating != None and g.white.rating > 0:
            n+=1
            performance += g.white.rating
            if g.result == 2: performance += 400
            elif g.result == 1 : performance -= 400
    if n > 0:
        performance /= n
    return performance


# for updating standings
def standings_save(instance):
        league = League.objects.get(pk=instance.pk)
        league.updated_date = datetime.datetime.now()
        league.save()
        for player in league.players.all():
            obj, created = Standings.objects.get_or_create(league = league, player = player)
            if created:
                obj.rating = player.rating
                obj.save()
        
        standings = Standings.objects.filter(league = league).exclude(player__in = league.players.all())
        for player in standings:
                player.delete()

def standings_position_update(league):
    order = STANDINGS_ORDER[league.standings_order][1]
    standings = Standings.objects.filter(league = league.pk).order_by(*order)
    position = 0
    for player in standings:
        position += 1
        player.position = position
        player.save()

def standings_update(instance):
        standings = Standings.objects.filter(league = instance.pk)
        # to calculate NBS and Buchholz score
        player_wins   = {}
        player_losses = {}
        player_draws  = {}
        player_points = {}
        player_ratings = {}

        for standing in standings:
            points = 0
            wins = 0
            winswblack = 0
            lost = 0
            draws = 0
            matches = 0
            matcheswblack = 0
            form = ''
            player = standing.player
            wins_against   = []
            draws_against  = []
            lost_against   = []
            player_schedule = Schedule.objects.filter(~Q(result=3) & (Q(white=player) | Q(black=player)), league = instance.pk).order_by('-date')
            nrounds = len(instance.get_rounds())
            for i,match in enumerate(player_schedule):
                matches += 1
                if match.white == player:
                    if match.result == 1 :
                        if (instance.get_format_display() == "Swiss" and i < 20) or i < 5:
                            form = 'W' + form
                        wins += 1
                        points += instance.get_win_points_display()
                        wins_against += [ match.black ]
                    elif match.result == 2 :
                        lost += 1
                        if (instance.get_format_display() == "Swiss" and i < 20) or i < 5:
                            form = 'L' + form
                        points += instance.get_lost_points_display()
                        lost_against += [ match.black ]
                    else:
                        draws += 1
                        if (instance.get_format_display() == "Swiss" and i < 20) or i < 5:
                            form = 'D' + form
                        points += instance.get_draw_points_display()
                        draws_against += [ match.black ]

                if match.black == player:
                    matcheswblack += 1
                    if match.result == 2 :
                        if (instance.get_format_display() == "Swiss" and i < 20) or i < 5:
                            form = 'W' + form
                        wins += 1
                        winswblack += 1
                        points += instance.get_win_points_display()
                        wins_against += [ match.white ]
                    elif match.result == 1 :
                        if (instance.get_format_display() == "Swiss" and i < 20) or i < 5:
                            form = 'L' + form
                        lost += 1
                        points += instance.get_lost_points_display()
                        lost_against += [ match.white ]
                    elif match.result == 0:
                        draws += 1
                        if (instance.get_format_display() == "Swiss" and i < 20) or i < 5:
                            form = 'D' + form
                        points += instance.get_draw_points_display()
                        draws_against += [ match.white ]

            standing.form = form
            # if we're in a Swiss, paired rounds should also be added as P
            if instance.get_format_display() == "Swiss":
                while len(standing.form) < nrounds:
                    standing.form = standing.form+'P'
            standing.points = points
            standing.win = wins
            standing.win1 = winswblack
            standing.lost = lost
            standing.draws = draws
            standing.matches = matches
            standing.matches1 = matcheswblack

            # save these to calculate the NBS tie break score
            player_points[player] = points
            player_ratings[player] = standing.rating if standing.rating else 0
            player_draws[player] = draws_against
            player_losses[player] = lost_against
            player_wins[player] = wins_against

        for standing in standings:
            nbs = 0
            opponent_scores = []
            opponent_ratings = []
            for p in player_draws[standing.player]:
                if p in player_points.keys():
                    nbs += 0.5 * player_points[p]
                    opponent_scores += [ player_points[p]]
                    opponent_ratings += [ player_ratings[p]]
            for p in player_wins[standing.player]:
                if p in player_points.keys():
                    nbs += 1.0 * player_points[p]
                    opponent_scores += [ player_points[p]]
                    opponent_ratings += [ player_ratings[p]]

            for p in player_losses[standing.player]:
                if p in player_points.keys():
                    opponent_scores += [ player_points[p]]
                    opponent_ratings += [ player_ratings[p]]
            if len (opponent_scores) > 0:
                standing.buchholz = sum(opponent_scores)
                standing.buchholzcut1 = standing.buchholz - min(opponent_scores)
                standing.opprating = (sum(opponent_ratings) - min(opponent_ratings)) / max(1, len(opponent_ratings) - 1)
                standing.performance = get_performance_score(standing.player, instance)
            else:
                standing.buchholz = 0
                standing.buchholzcut1 = 0
                standing.opprating = 0
                standing.performance = 0
            standing.nbs = nbs
            standing.save()

        standings_position_update(instance)


# for makign tournaments

from swissdutch.constants import Colour, FloatStatus
from swissdutch.player import Player as PairingPlayer

import random, operator, copy

def get_last_round(league):
    '''
    Format a tuple of Paired Players from last round of league for SwissDutch Pairing
    '''
    order = ('-rating','player__surename')
    standings = Standings.objects.filter(league = league.pk)
    #standings = Standings.objects.filter(league = league).order_by('-rating')
    paired_players = {}
    for i,p in enumerate(standings):
        paired_players[p.player] = PairingPlayer(name=p.player.__str__(),
            rating=p.rating,
        )
    # the first round in the dutch pairing re-order pairing numbers
    # copy the logic here for consistency
    players = list(paired_players.values())
    players.sort(key=operator.attrgetter('name'))
    players.sort(key=operator.attrgetter('rating', 'title'),reverse=True)
    for i,p in enumerate(players): p.pairing_no = i+1
    rounds = league.get_rounds()
    games = Schedule.objects.filter(league = league)
    if len(rounds) > 0 :
        for i,r in enumerate(rounds):
            round_games = games.filter(round=r)
            for game in round_games:
                if game.result == 3: continue
                if game.black == None:
                    #white has received a bye
                    white = paired_players[game.white]
                    white._colour_hist += (Colour.none,)
                    white._opponents += (0,)
                    if game.result == 0:
                        white._score += league.draw_points
                    elif game.result == 1:
                        white._score += league.win_points
                    elif game.result == 2:
                        white._score += league.lost_points

                elif game.white == None:
                    #black has received a bye
                    black = paired_players[game.black]
                    black._colour_hist += (Colour.none,)
                    black._opponents += (0,)
                    if game.result == 0:
                        black._score += league.draw_points
                    elif game.result == 1:
                        black._score += league.lost_points
                    elif game.result == 2:
                        black._score += league.win_points

                else:
                    white = paired_players[game.white]
                    black = paired_players[game.black]

                    white._colour_hist += (Colour.white,)
                    black._colour_hist += (Colour.black,)
                    white._opponents += (black.pairing_no,)
                    black._opponents += (white.pairing_no,)

                    # reset all prevs to none
                    if white._float_status == FloatStatus.downPrev:
                        white._float_status = FloatStatus.none
                    if white._float_status == FloatStatus.upPrev:
                        white._float_status = FloatStatus.none
                    if black._float_status == FloatStatus.downPrev:
                        black._float_status = FloatStatus.none
                    if black._float_status == FloatStatus.upPrev:
                        black._float_status = FloatStatus.none


                    # set all up or downs to prevup and prevdown
                    if white._float_status == FloatStatus.down:
                        white._float_status = FloatStatus.downPrev
                    if white._float_status == FloatStatus.up:
                        white._float_status = FloatStatus.upPrev
                    if black._float_status == FloatStatus.down:
                        black._float_status = FloatStatus.downPrev
                    if black._float_status == FloatStatus.up:
                        black._float_status = FloatStatus.upPrev
                

                    # based on current scores before round, so do before
                    # modifying scores
                    if white.score > black.score:
                        white._float_status=FloatStatus.down
                        black._float_status=FloatStatus.up
                    elif white.score < black.score:
                        white._float_status=FloatStatus.up
                        black._float_status=FloatStatus.down

                    if game.result == 0:
                        white._score += league.draw_points
                        black._score += league.draw_points
                    elif game.result == 1:
                        white._score += league.win_points
                        black._score += league.lost_points
                    elif game.result == 2:
                        white._score += league.lost_points
                        black._score += league.win_points
                
    return paired_players


def get_next_round(round_no, engine, last_round = False, byes = None):
    bye_players = []
    to_pair = copy.copy(last_round)
    if byes:
        for b in byes:
            bye_players += [ [b,to_pair.pop(b)] ]

    # use name as the inverse dictionary key to avoid possibility of pairing numer
    # being changed, e.g. first round
    ivd = {v.name: k for k, v in last_round.items()}

    paired_players = engine.pair_round(round_no, tuple(to_pair.values()), last_round = last_round)
    
    next_round = { ivd[pp.name].pk : pp for pp in paired_players }
    for b in bye_players:
        b[1]._colour_hist += (Colour.none,)
        b[1]._opponents   += (0,)
        # to avoid any issue with non unique pairing numbers
        b[1].pairing_no = -1 * b[1].pairing_no
        next_round[b[0].pk] = b[1]
    return next_round

def get_pairs(paired_players):
    # we need an inverse dictionary to get opponents
    ivd = {v.pairing_no: k for k, v in paired_players.items()}
    pairs, id_pairs = (), ()
    for p,pp in paired_players.items():
        if pp.colour_hist[-1] == Colour.white and pp.opponents[-1] != 0:
            player = Player.objects.get(pk = p)
            opponent = Player.objects.get(pk = ivd[pp.opponents[-1]])
            pairs += ((player,opponent),)
            id_pairs += ((p, ivd[pp.opponents[-1]]),)
        elif pp.opponents[-1] == 0:
            player = Player.objects.get(pk = p)
            pairs += ((player,None),)
            id_pairs += ((p,0),)
    return pairs, id_pairs

def create_games_from_id_pairs(league, round_no, pairs, date):
    games = []
    for p in pairs:
        player = Player.objects.get(pk = p[0])
        opponent = None
        if p[1] != 0:
            opponent = Player.objects.get(pk = p[1])
        g = Schedule(league=league,round = round_no,white=player,black=opponent, date = date)
        if opponent == None : g.result = 0
        games += [ g ]
    return games

def create_games_from_pairs(league, round_no, pairs, date):
    games = []
    for p in pairs:
        games += [ Schedule(league=league,round = round_no,white=p[0],black=p[1], date = date) ]
    return games


def create_games(league, round_no, paired_players, date):
    # we need an inverse dictionary to get opponents
    pairs,_ = get_pairs(paired_players)
    games = create_games_from_pairs(league, round_no, pairs, date)
    return games




def top_seed_colour_selection():
    return Colour.white

'''
def test_swiss(league, nrounds):
    # this is a test which, for aims to see if keeping track of the rounds is the same as
    # creating from the database anew each round
    persistent_pairings = ()
    first_db_pairings = {}
    games_to_delete = []
    engine  = DutchPairingEngine(top_seed_colour_selection_fn = top_seed_colour_selection)
    for i in range(nrounds):
        last_round = get_last_round(league)
        if i == 0 :
            persistent_pairings = tuple([t for t in last_round.values()])
            first_db_pairings   = { p : v.pairing_no for p,v in last_round.items()  }
        new_pairings = tuple([t for t in last_round.values()])
        #assert(all([a in b for a, b in zip(persistent_pairings, new_pairings)]))
        #for a,b in zip(persistent_pairings, new_pairings):
        #    print(a.pairing_no, a.score,a._float_status, a.opponents,b.pairing_no,b.score,b.opponents, b._float_status)
'''
'''
        for a in persistent_pairings:
            for b in new_pairings:
                if a.pairing_no == b.pairing_no:
                    if a != b:
                        print("%s is not equal to %s for recalculated pairings"%(a.name,b.name))
                        #print(a._float_status,b._float_status)
                        #print(a.score,b.score)
                        #print(a.opponents,b.opponents)
                        print(a.colour_hist,b.colour_hist)
                    else:
                        print("%s is equal to %s for recalculated "%(a.name,b.name))
                        print(a.colour_hist,b.colour_hist)
'''
'''
        persistent_pairings = engine.pair_round(i+1, persistent_pairings)
        next_round = get_next_round(i+1, engine, last_round)
'''
'''

        for a in persistent_pairings:
            for b in tuple(next_round.values()):
                if a.pairing_no == b.pairing_no:
                    if a != b:
                        print("%s is not equal to %s for continued pairings"%(a.name,b.name))
                        #print(a._float_status,b._float_status)
                        #print(a.score,b.score)
                        #print(a.opponents,b.opponents)
                        print(a.colour_hist,b.colour_hist)
                    else:
                        print("%s is equal to %s for continued "%(a.name,b.name))
                        print(a.colour_hist,b.colour_hist)
                        
'''
'''
        games = create_games(league, i+1, next_round, datetime.now())
        games_to_delete += games
        for g in games:
            result = random.choice([0,1,2])
            g.result = result
            g.save()
            print(g)
            # the persistent pairing has not changed form initial pairing numbers
            white_pairing_no = first_db_pairings[g.white] if g.white else 0
            black_pairing_no = first_db_pairings[g.black] if g.black else 0
            for pp in persistent_pairings:
                if white_pairing_no != 0 and pp.pairing_no == white_pairing_no:
                    if result == 0 : pp._score += 1
                    elif result == 1 : pp._score += 2
                if black_pairing_no != 0 and pp.pairing_no == black_pairing_no:
                    if result == 0 : pp._score += 1
                    elif result == 2 : pp._score += 2
        standings_save(league)
        standings_update(league)

    #for g in games_to_delete:
    #    g.delete()
    #standings_save(obj)
    #standings_update(obj)
'''

def create_balanced_round_robin(players):
    """ Create a schedule for the players in the list and return it"""
    s = []
    if len(players) % 2 == 1: players = players + [None]
    # manipulate map (array of indexes for list) instead of list itself
    # this takes advantage of even/odd indexes to determine home vs. away
    n = len(players)
    map = list(range(n))
    mid = n // 2
    for i in range(n-1):
        l1 = map[:mid]
        l2 = map[mid:]
        l2.reverse()
        round = []
        revround = []
        for j in range(mid):
            t1 = players[l1[j]]
            t2 = players[l2[j]]
            if j == 0 and i % 2 == 1:
                # flip the first match only, every other round
                # (this is because the first match always involves the last player in the list)
                round.append((t2, t1))
                revround.append((t1,t2))
            else:
                round.append((t1, t2))
                revround.append((t2,t1))
        s.append(round)
        s.append(revround)
        # rotate list by n/2, leaving last element at the end
        map = map[mid:-1] + map[:mid] + map[-1:]
    return s

def create_round_robin_games(league,rounds,dates):
    if isinstance(dates,datetime) or len(dates) == 1:
        dates = [dates[0]] * len(rounds)
    for round_no,(date,pairs) in enumerate(zip(dates,rounds)):
        games = create_games_from_pairs(league, round_no+1, pairs, date)
        for g in games: g.save()

def create_round_robin(league, dates):
    rounds = create_balanced_round_robin(list(league.players.all()))
    create_round_robin_games(league,rounds,dates)


# figure making
import matplotlib
import matplotlib.image as image
import os
from matplotlib import pyplot as plt
from matplotlib import table
matplotlib.use("pdf") ## Include this line to make PDF output

from django.templatetags.static import static
from django.conf import settings

from itertools import cycle

def make_table(league):
    fig, (ax1, ax2) = plt.subplots(figsize=(8.27, 11.69), nrows=2, gridspec_kw={'height_ratios': [1, 19], 'hspace' : 0.15})
    ax1.set_axis_off()
    ax2.set_axis_off()
    standings = Standings.objects.filter(league = league)
    ax2.text(0.5, 1.02, league, horizontalalignment='center', verticalalignment='center', fontsize=20.0)
    table = ax2.table(
        cellText = [ [s.player, s.matches, s.win, s.draws, s.lost, s.points ] for s in standings],
        colLabels = ['Name', 'P', 'W', 'D', 'L', 'Pts'],
        colWidths = [0.4, 0.12, 0.12, 0.12, 0.12, 0.12],
        cellLoc ='center',  
        cellColours = [ [c for i in range(6)] for j,c in zip(range(len(standings)),cycle([(1,1,1,1.0), (0,0,0,0.1)])) ],
        loc ='upper left',
        rowLabels = [ s.position for s in standings ],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table_props = table.properties()
    for i,c in table_props['celld'].items():
        c.set_height(0.03)


    ax2.text(0.5, 0.1, "Last updated on %s"%(league.updated_date.date().strftime('%d %b %Y')), horizontalalignment='center', verticalalignment='center')

    im = image.imread(settings.BASE_DIR + static('img/wcc_logo_outline.png'))
    ax1.imshow(im)

    return fig

import matplotlib as mpl

def hide_edges(table, idx0, idx1):
    ix0,ix1 = np.asarray(idx0), np.asarray(idx1)
    d = ix1 - ix0
    if not (0 in d and 1 in np.abs(d)):
        raise ValueError("ix0 and ix1 should be the indices of adjacent cells. ix0: %s, ix1: %s" % (ix0, ix1))

    if d[0]==-1:
        edges = ('BRL', 'TRL')
    elif d[0]==1:
        edges = ('TRL', 'BRL')
    elif d[1]==-1:
        edges = ('BTR', 'BTL')
    else:
        edges = ('BTL', 'BTR')

    # hide the merged edges
    for ix,e in zip((ix0, ix1), edges):
        table[ix[0], ix[1]].visible_edges = e


def mergecells(table, idx0, idx1):
    ix0,ix1 = np.asarray(idx0), np.asarray(idx1)
    hide_edges(table, idx0, idx1)
    txts = [table[ix[0], ix[1]].get_text() for ix in (ix0, ix1)]
    tpos = [np.array(t.get_position()) for t in txts]

    # center the text of the 0th cell between the two merged cells
    trans = (tpos[1] - tpos[0])/2
    if trans[0] > 0 and txts[0].get_ha() == 'right':
        # reduce the transform distance in order to center the text
        trans[0] /= 2
    elif trans[0] < 0 and txts[0].get_ha() == 'right':
        # increase the transform distance...
        trans[0] *= 2

    print('trans', tpos[0], tpos[1], trans, txts)
    txts[0].set_transform(mpl.transforms.Affine2D().translate(*trans))

    # hide the text in the 1st cell
    txts[1].set_visible(False)

def make_crosstable(league):
    fig, (ax1, ax2) = plt.subplots(figsize=(11.69, 8.27), nrows=2, gridspec_kw={'height_ratios': [1, 19], 'hspace' : 0.15})
    plt.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.05)
    ax1.set_axis_off()
    ax2.set_axis_off()
    standings = Standings.objects.filter(league = league)
    games     = Schedule.objects.filter(league=league)
    ax2.text(0.5, 1.02, league, horizontalalignment='center', verticalalignment='center', fontsize=20.0)

    cellTexts, rowLabels = [], []
    cellColours = []
    colLabels = ['Name'] + [str(i+1) for i in range(len(standings))] + ['P','W','D','L','Pts' ]
    for i,p1 in enumerate(standings):
        p1_white_games = games.filter(white = p1.player)
        p1_black_games = games.filter(black = p1.player)

        rowTexts = [ p1.player ]
        rowLabels += [ p1.position ]
        rowColour = [ (1, 1, 1, 1.0) ]
        for p2 in standings:
            p1_p2_white_games = p1_white_games.filter(black = p2.player)
            p1_p2_black_games = p1_black_games.filter(white = p2.player)
            if len(p1_p2_white_games) == 1:
                points_text = '%i\n'%(p1_p2_white_games[0].get_white_points())
            else:
                points_text = '\n'
                
            if len(p1_p2_black_games) == 1:
                points_text += '%i'%(p1_p2_black_games[0].get_black_points())
                
            rowTexts += [ points_text ]

            if p1.player == p2.player: rowColour += [ (0,0,0,0.2)]
            else: rowColour += [(1,1,1,1.0)]
        rowTexts += [ p1.matches, p1.win, p1.draws, p1.lost, '%i'%(p1.points) ]
        rowColour += [(1,1,1,1.0), (1,1,1,1.0), (1,1,1,1.0), (1,1,1,1.0), (1,1,1,1.0)]
        cellColours += [ rowColour ]
        cellTexts += [ rowTexts ]


    crosstable = ax2.table(
        cellText = cellTexts,
        colLabels = colLabels,
        colWidths = [0.2] + len(standings) * [ (1.0 - 0.2 - 0.05*5)/len(standings) ] + ([ 0.05]*5),
        cellColours = cellColours,
        cellLoc ='center',  
        #cellColours = [ [c for i in range(6)] for j,c in zip(range(len(standings)),cycle([(1,1,1,1.0), (0,0,0,0.1)])) ],
        loc ='upper left',
        rowLabels = rowLabels,
    )
    
    crosstable.auto_set_font_size(False)
    crosstable.set_fontsize(min(10, int(200.0/len(standings))))
    crosstable_props = crosstable.properties()
    for i,c in crosstable_props['celld'].items():
        c.set_height(min(0.06,0.9/len(standings)))

    cells = [key for key in crosstable._cells if ((key[1] in [-1,0] + [ len(standings) + i for i in [1,2,3,4,5] ]) or (key[0] == 0)) ]
    for cell in cells:
        crosstable._cells[cell].get_text().set_ha('right')
        font_size = min(14, int(280.0/len(standings)))
        text_size = len(crosstable._cells[cell].get_text().get_text())
        # reduce font size if we really have a lot of text
        if text_size > 15:
            font_size = 15.0 / text_size * font_size


        crosstable._cells[cell].set_fontsize(font_size)
    '''
    
    for i in range(len(standings)):
        for j in (-1,0):
            mergecells(crosstable, (i*2+1,j), (i*2+2,j))
        for j in range(6):
            mergecells(crosstable, (i*2+1,len(standings)+j), (i*2+2, len(standings)+j))
        for j in range(len(standings)):
            hide_edges(crosstable, (i*2+1, j+1), (i*2+2,j+1))
    '''
    #ax2.add_table(crosstable)
    ax2.text(0.5, 0.01, "Last updated on %s"%(league.updated_date.date().strftime('%d %b %Y')), horizontalalignment='center', verticalalignment='center')

    im = image.imread(settings.BASE_DIR + static('img/wcc_logo_outline.png'))
    ax1.imshow(im)

    return fig

