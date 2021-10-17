from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, League, Player, Season, STANDINGS_ORDER
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render
import datetime

class TeamRoster(ListView):
    template_name = 'roster.html'
    model = Player
    context_object_name = 'roster'
    def get_context_data(self, **kwargs):
        context = super(TeamRoster, self).get_context_data(**kwargs)
        
        season_name = ''
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
        else:
            season = Season.objects.all().first()
        season_pk = season.pk
        season_name = ": {} {}".format(season.name, season.name)


        context['table_name'] = season_name
        context['slug'] = self.kwargs.get('season')
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
        else:
            season = Season.objects.all()[0]
        season_pk = season.pk
        season_name = season.name
        qs = self.model.objects.filter(seasons=season_pk).order_by('-rating')

        return qs

class StandingsFull(ListView):
    template_name = 'standings.html'
    model = Standings
    context_object_name = 'standings'

    def get_context_data(self, **kwargs):
        context = super(StandingsFull, self).get_context_data(**kwargs)
        
        league_name = ''
        last_updated = 'test'
        print(self.kwargs)
        if self.kwargs.get('league'):
            league = League.objects.get(slug=self.kwargs['league'])
            league_pk = league.pk
            league_format = league.format
            league_name = ": {} {}".format(league.season.name, league.name)
            last_updated = league.updated_date
        

        context['last_updated'] = last_updated
        context['table_name'] = league_name
        context['league_format'] = league_format
        context['slug'] = self.kwargs.get('league')
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        if self.kwargs.get('league'):
            league = League.objects.get(slug=self.kwargs['league'])
            league_pk = league.pk
            league_name = league.name
            order = STANDINGS_ORDER[league.standings_order][1]
            qs = self.model.objects.filter(league=league_pk).order_by(*order)
        return qs

class ScheduleFull(ListView):
    template_name = 'schedule.html'
    model = Schedule
    context_object_name = 'schedule'

    def get_context_data(self, **kwargs):
        context = super(ScheduleFull, self).get_context_data(**kwargs)
        
        league_name = ''
        if self.kwargs.get('league'):
            league = League.objects.get(slug=self.kwargs['league'])
            league_pk = league.pk
            league_name = ": {} {}".format(league.season, league.name)
            context['page_name'] = _('Schedule')
            context['league'] = league_name
            context['slug'] = self.kwargs.get('league')
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        if self.kwargs.get('league'):
            league = League.objects.get(slug=self.kwargs['league'])
            league_pk = league.pk
            league_name = league.name
            qs = self.model.objects.filter(league=league_pk).order_by('-date')
        return qs

'''
class PlayerSchedule(ListView):
    template_name = 'games.html'
    model = Schedule
    context_object_name = 'schedule'
    
    def get_context_data(self, **kwargs):
        context = super(PlayerSchedule, self).get_context_data(**kwargs)
        if self.kwargs.get('player'):
            player = Player.objects.get(id=self.kwargs['player'])
            context['player'] = player
        
        if self.kwargs.get('league'):
            league = League.objects.get(slug=self.kwargs['league'])
            context['league'] = league
        context['page_name'] = _('Schedule')      
        
        return context


    def get_queryset(self, *args, **kwargs):
        if self.kwargs.get('player') and not self.kwargs.get('league'):
            player_pk = Player.objects.get(id=self.kwargs.get('player')).pk
            #qs = self.model.objects.filter(Q(white=player_pk) | Q(black=player_pk)).order_by('date')
            toReturn = {}
            games = {}
            league_pk = league.pk
            league_name = league.name
            player = Player.objects.get(id=self.kwargs.get('player'))
            
            if not self.kwargs.get('league'):
                season = Season.objects.last()
                for league in season.leagues:
                    season_league_games = self.model.objects.filter(Q(white=player) | Q(black=player), league = league ).order_by('-date')
                    if len(season_league_games) > 0:
                        if season not in games.keys(): games[season] = {}
                        games[season][league] = season_league_games
            else:
                league = League.objects.get(id = self.kwargs.get('league'))
                season = league.season
                season_league_games = self.model.objects.filter(Q(white=player) | Q(black=player), league = league ).order_by('-date')
                games[season][league] = season_league_games
            toReturn['player'] = player
            toReturn['games'] = games
        return toReturn

'''

# Create your views here.

def fixtures(request, league, **kwargs):
    l = get_object_or_404(League, slug=league)
    games = Schedule.objects.filter(league=l)
    #let's decide how to break this down, if we have rounds, do that
    #else we group by date
    rounds = set([ g.round for g in games if g.round != None])
    dates = sorted(set([ g.date.date() for g in games if g.date != None]))
    games_display = {}
    useRounds = (len(rounds) > 0)
    latest = None
    if len(rounds) > 0:
        latest = list(rounds)[0]
        pccurrcomplete = 0 
        pcprevcomplete = 0
        for r in rounds:
            #games_round = games.filter(Q(round=r) & ~Q(black=None) & ~Q(white=None)).order_by('date')
            games_round = games.filter(round=r).order_by('date')
            games_display[r] = games_round
            #now find which round to show, the last complete one
            pcprevcomplete = pccurrcomplete
            ncomplete = 0
            for g in games_round:
                if g.result != 3: ncomplete += 1
            pccurrcomplete = float(ncomplete) / len(games_round)
            if pcprevcomplete == 1.0 or pccurrcomplete > 0:
                latest = r
    else:
        # no rounds, let's organise by date instead
        #games_display['rounds'] = False
        if len(dates) > 0:
            for d in dates:
                games_date = games.filter(date__date = d).order_by('date')
                games_display[d] = games_date
            today = datetime.datetime.today().date()
            prev_dates = [d for d in dates if d < today]
            latest = max(prev_dates) if len(prev_dates) > 0 else dates[0]

    #let's get the standings now
    order = STANDINGS_ORDER[l.standings_order][1]
    standing = Standings.objects.filter(league=l).order_by(*order)
    return render(request, 'fixtures.html', {'games': games_display, 'useRounds' : useRounds, 'latest' : latest, 'standings' : standing, 'league' : l })


def player(request, player_id, **kwargs):
    player = get_object_or_404(Player, id=player_id)
    games = {}
    if 'league' in kwargs:
        league = get_object_or_404(League, slug=kwargs['league'])
        games[league.season] = {}
        games[league.season][league] = Schedule.objects.filter((Q(white=player_id) | Q(black=player_id)) & Q(league = league)).order_by('date')
    else:
        season = Season.objects.last()
        
        if player in season.players.all(): games[season] = {}
        for league in season.league_set.all():
            league_pk = league.pk
            season_league_games  = Schedule.objects.filter(Q(white=player_id) | Q(black=player_id), league = league_pk).order_by('date')
            if len(season_league_games) > 0:
                if season not in games.keys(): games[season] = {}
                games[season][league]  = season_league_games
        
    return render(request, 'games.html', {'player': player, 'games': games})

def game(request, game_id):
    f = get_object_or_404(Schedule, id=game_id)
    return render(request, 'game.html', {'game': f})

def season_summary(request, season_slug):
    f = get_object_or_404(Season, slug = season_slug)
    return render(request, 'league.html', {'season' : f, 'leagues' : League.objects.filter(season=f)})

def index(request):
    season_slug = Season.objects.all().last().slug
    return season_summary(request, season_slug)



# these views are used in the admin


from io import BytesIO


from django.http import HttpResponse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.safestring import mark_safe

from .forms import LichessArenaForm, LichessSwissForm, LichessGameForm, RoundForm, PrintRoundForm, RoundRobinForm, ScheduleModelFormset, ClubNightForm

import utils

from swissdutch.dutch import DutchPairingEngine
from .utils import get_arena_games, get_swiss_games, get_game, make_table_pdf, standings_save, standings_update


def download_league_pdf(request, id, admin_site):
    obj = League.objects.get(pk=id)
    response = HttpResponse(content_type='application/pdf')
    filename = '%s_%s'%(obj,obj.updated_date.date())
    response['Content-Disposition'] = 'attachement; filename={0}.pdf'.format(filename)
    buffer = BytesIO()
    fig = make_table_pdf(obj)
    fig.savefig(buffer, format='pdf')
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def manage_league_view(request, id, admin_site ):
    opts       = League._meta
    arena_form = LichessArenaForm()
    swiss_form = LichessSwissForm()
    game_form  = LichessGameForm()
    round_form = PrintRoundForm()
    obj = League.objects.get(pk=id)
    rounds = obj.get_rounds()
    round_form.fields['round_no'].choices=tuple((i,i) for i in rounds)

    ngames = 0
    nchanges = 0
    if request.POST:
        games = {}
        if request.POST.get('lichess_arena_id') is not None:
            games.update(get_arena_games(request.POST.get('lichess_arena_id')))
        if request.POST.get('lichess_swiss_id') is not None:
            games.update(get_swiss_games(request.POST.get('lichess_swiss_id')))
        if request.POST.get('lichess_game_id') is not None:
            games.update(get_game(request.POST.get('lichess_game_id')))
        if request.POST.get('round_no') is not None:
            message = ''
            for g in Schedule.objects.filter(league=obj,round=request.POST.get('round_no')):
                if g.white and g.black:
                    if g.get_result_display() =='-':
                        message += '%s ( %s ) v %s ( % s ) <br/>'%(g.white, g.white.lichess, g.black, g.black.lichess)
                    else:
                        message += '%s %s %s <br/>'%(g.white, g.get_result_display(), g.black)

            admin_site.message_user(request,mark_safe(message))
        for g,v in games.items():
            if len(Schedule.objects.filter(lichess=g)) > 0:
                schedule = Schedule.objects.filter(lichess=g)[0]
                if schedule.league != obj:
                    admin_site.message_user(request,'Game between %s and %s is in %s, changing to %s'%(v['white'],v['black'],schedule.league,obj))
                    schedule.league = obj
                    schedule.save()
                    nchanges += 1
                else :
                    admin_site.message_user(request,'Game between %s and %s is already in the database'%(v['white'],v['black']))
                continue
            white = Player.objects.filter(lichess=v['white'])
            black = Player.objects.filter(lichess=v['black'])
            if len(white) == 0:
                admin_site.message_user(request,'Player %s is not in the database, skipping game' %(v['white']))
                continue
            if len(black) == 0:
                admin_site.message_user(request,'Player %s is not in the database, skipping game' %(v['black']))
                continue
            if white[0] not in obj.players.all():
                admin_site.message_user(request, 'Warning: Player %s is in the database but not the league' %(v['white']))
            if black[0] not in obj.players.all():
                admin_site.message_user(request, 'Warning: Player %s is in the database but not the league' %(v['black']))
            schedule = Schedule(league=obj,lichess=g,white=white[0],black=black[0],date=v['date'],result=v['result'])
            if 'pgn' in v.keys():
                schedule.pgn = v['pgn']
            schedule.save()
            ngames+=1
        if ngames + nchanges > 0 :
            standings_save(obj)
            standings_update(obj)

        admin_site.message_user(request, 'added %i games to %s'%(ngames + nchanges,obj))

    if not admin_site.has_change_permission(request, obj):
        raise PermissionDenied

    # do cool management stuff here

    preserved_filters = admin_site.get_preserved_filters(request)
    form_url = request.build_absolute_uri()
    form_url = request.META.get('PATH_INFO', None)

    form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

    context = {
        'title': 'Manage %s' % obj,
        'has_change_permission': admin_site.has_change_permission(request, obj),
        'opts': opts,
        #'errors': form.errors,
        'app_label': opts.app_label,
        'original': obj,
        'form_url' : form_url,
        'arena_form' : arena_form,
        'swiss_form' : swiss_form,
        'round_form' : round_form,
        'game_form' : game_form
    }

    return render(request, admin_site.manage_view_template, context)

def create_round_robin_view(request, id, admin_site ):
    opts = League._meta
    obj = League.objects.get(pk=id)
    form = RoundRobinForm()
    preserved_filters = admin_site.get_preserved_filters(request)
    form_url = request.build_absolute_uri()
    form_url = request.META.get('PATH_INFO', None)

    form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

    context = {
            'title': 'Create Round Robin for %s' % obj,
            'has_change_permission': admin_site.has_change_permission(request, obj),
            'opts': opts,
            'form' : form,
            #'errors': form.errors,
            'app_label': opts.app_label,
            'original': obj,
            'form_url' : form_url,
    }
    if request.POST and request.POST.get('create_round_robin') is not None:
        # create it and send it back for confirmation
        admin_site.message_user(request, 'Created Round Robin Games')
        date = request.POST.get('datetime_0')
        time = request.POST.get('datetime_1')
        round_date = datetime.datetime.strptime('%s %s'%(date,time), '%Y-%m-%d %H:%M:%S')
        games = utils.create_round_robin(obj, [ round_date ])

        #context['pairs'] = pairs
        #context['round'] = next_round_no
        #context['date'] = date
        #context['time'] = time
        #request.session['pairs'] = id_pairs

    if not admin_site.has_change_permission(request, obj):
        raise PermissionDenied

    return render(request, admin_site.create_round_robin_template, context)

def create_round_view(request, id, admin_site ):
    opts = League._meta
    obj = League.objects.get(pk=id)
    form = RoundForm()
    form.fields['byes'].queryset = obj.players
    preserved_filters = admin_site.get_preserved_filters(request)
    form_url = request.build_absolute_uri()
    form_url = request.META.get('PATH_INFO', None)

    form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

    context = {
            'title': 'Create Round for %s' % obj,
            'has_change_permission': admin_site.has_change_permission(request, obj),
            'opts': opts,
            'form' : form,
            #'errors': form.errors,
            'app_label': opts.app_label,
            'original': obj,
            'form_url' : form_url,
    }
    if request.POST and request.POST.get('create_swiss_games'):
        # rond has been paired and confirmed, make the games
        id_pairs = request.session.get('pairs')
        request.session['pairs'] = ()
        date = request.POST.get('date')
        time = request.POST.get('time')
        round_date = datetime.datetime.strptime('%s %s'%(date,time), '%Y-%m-%d %H:%M:%S')
        roundno = request.POST.get('round')
        games = utils.create_games_from_id_pairs(obj, roundno, id_pairs, round_date)
        for g in games:
            if g.white == None: admin_site.message_user(request, '%s will get a bye'%(g.black))
            if g.black == None: admin_site.message_user(request, '%s will get a bye'%(g.white))
            else: admin_site.message_user(request, '%s will play %s'%(g.white, g.black))
            g.save()
        utils.standings_position_update(obj)


    elif request.POST and request.POST.get('create_swiss_round') is not None:
        # here we've been asked to create a round

        # check if it's legal (more checks should be added)
        unfinished_games = Schedule.objects.filter(league=obj,result=3)
        if len(unfinished_games) > 0 :
            admin_site.message_user(request, "There are %i unfinished games, can't create new round!"%(len(unfinished_games)))
        else:
            # create it and send it back for confirmation
            date = request.POST.get('datetime_0')
            time = request.POST.get('datetime_1')
            round_date = datetime.datetime.strptime('%s %s'%(date,time), '%Y-%m-%d %H:%M:%S')
            rounds = obj.get_rounds()
            standings = Standings.objects.filter(league = obj)
            next_round_no = 1
            if len(rounds) > 0 : next_round_no = rounds[-1] + 1
            engine  = DutchPairingEngine()
            last_round = utils.get_last_round(obj)
            byes = []
            if request.POST.get('byes'):
                for p in request.POST.get('byes'):
                    player = Player.objects.get( id = p)
                    byes += [ player ]
            next_round = utils.get_next_round(next_round_no, engine, last_round, byes = byes )
            pairs, id_pairs = utils.get_pairs(next_round)
            context['pairs'] = pairs
            context['round'] = next_round_no
            context['date'] = date
            context['time'] = time
            request.session['pairs'] = id_pairs

    if not admin_site.has_change_permission(request, obj):
        raise PermissionDenied

    return render(request, admin_site.create_round_template, context)


def manage_schedule_view(request, id, admin_site ):
    opts = Schedule._meta
    game_form = LichessGameForm()
    obj = Schedule.objects.get(pk=id)
    if request.POST:
        if request.POST.get('lichess_game_id') is not None:
            game_id = request.POST.get('lichess_game_id')
            game = utils.get_game(game_id)
            white = obj.white
            black = obj.black
        if game['white'] != obj.white.lichess:
            admin_site.message_user(request,'Note that lichess id %s does not correspond to current player %s' %(game['white'],obj.white))
            if game['black'] != obj.black.lichess:
                admin_site.message_user(request,'Note that lichess id %s does not correspond to current player %s' %(game['black'],obj.black))
            obj.lichess = game_id
            obj.date = game['date']
            obj.result = game['result']
            if 'pgn' in game.keys():
                obj.pgn = game['pgn']
            obj.save()
            utils.standings_save(obj.league)
            utils.standings_update(obj.league)

        admin_site.message_user(request, 'added lichess details to %s'%(obj))

    if not admin_site.has_change_permission(request, obj):
        raise PermissionDenied

        # do cool management stuff here
    preserved_filters = admin_site.get_preserved_filters(request)
    form_url = request.build_absolute_uri()
    form_url = request.META.get('PATH_INFO', None)

    form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

    context = {
        'title': 'Manage %s' % obj,
        'has_change_permission': admin_site.has_change_permission(request, obj),
        'opts': opts,
        #'errors': form.errors,
        'app_label': opts.app_label,
        'original': obj,
        'form_url' : form_url,
        'game_form' : game_form
    }

    return render(request, admin_site.manage_view_template, context)



def add_club_night_view(request, admin_site ):
    opts = Schedule._meta
    season = Season.objects.all().last()
    leagues = League.objects.filter(season=season)
    league = leagues.last()
    formset = ScheduleModelFormset(queryset=Schedule.objects.none(), initial = [{'league' : league}])
    for f in formset:
        f.fields['league'].choices = [ (l.id, l.__str__()) for l in leagues]
    clubnight_form = ClubNightForm()
    if not admin_site.has_change_permission(request, Schedule):
        raise PermissionDenied

    # do cool management stuff here
    preserved_filters = admin_site.get_preserved_filters(request)
    form_url = request.build_absolute_uri()
    form_url = request.META.get('PATH_INFO', None)

    form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

    context = {
        'title': 'Add Club Night',
        'has_change_permission': admin_site.has_change_permission(request, Schedule),
        'opts': opts,
        #'errors': form.errors,
        'app_label': opts.app_label,
        'form_url' : form_url,
        'clubnight_form' : clubnight_form,
        'formset' : formset
    }

    if request.POST:
        date = request.POST.get('datetime_0')
        time = request.POST.get('datetime_1')
        round_night = datetime.datetime.strptime('%s %s'%(date,time), '%Y-%m-%d %H:%M:%S')
        formset_result = ScheduleModelFormset(request.POST)
        admin_site.message_user(request, 'Added Club Night on %s at %s' %(date,time))
        for form in formset_result:
            game = form.save(commit = False)
            game.datetime = round_night
            game.save()
            admin_site.message_user(request, 'Added %s %s %s in the %s' %(game.white, game.get_result_display(), game.black, game.league))


    return render(request, admin_site.add_clubnight_template, context)
