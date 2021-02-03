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
        print(self.kwargs)
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
        else:
            print('getting last season')
            season = Season.objects.all().last()
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
            season = Season.objects.last()
            league_pk = league.pk
            league_name = league.name
            player = Player.objects.get(id=self.kwargs.get('player'))
            for league in season.leagues:
                season_league_games = self.model.objects.filter(Q(white=player) | Q(black=player), league = league ).order_by('-date')
                if len(season_league_games) > 0:
                    print(len(season_league_games))
                    if season not in games.keys(): games[season] = {}
                    games[season][league] = season_league_games
            toReturn['player'] = player
            toReturn['games'] = games
        return toReturn



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
    if useRounds:
        latest = list(rounds)[0]
        for r in rounds:
            games_round = games.filter(round=r).order_by('date')
            games_display[r] = games_round
            #now find which round to show, the last complete one
            ncomplete = 0
            for g in games_round:
                if g.result != 3: ncomplete += 1
            if float(ncomplete)/len(games_round) > 0.5:
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
    #query = request.GET.get('search')
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