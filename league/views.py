from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, League, Player, Season, STANDINGS_ORDER
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render

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
            season = Season.objects.all()[0]
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
        qs = self.model.objects.filter(seasons=season_pk).order_by('-grade')

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
            league_name = ": {} {}".format(league.season.name, league.name)
            last_updated = league.updated_date
        
        context['last_updated'] = last_updated
        context['table_name'] = league_name
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
    template_name = 'schedule.html'
    model = Schedule
    context_object_name = 'schedule'
     

    def get_context_data(self, **kwargs):
        context = super(PlayerSchedule, self).get_context_data(**kwargs)
        context['page_name'] = _('Archiwum')    
        if self.kwargs.get('player'):
            player = Player.objects.get(slug=self.kwargs['player'])
            context['player'] = player
        
        if self.kwargs.get('league'):
            league = League.objects.get(slug=self.kwargs['league'])
            context['league'] = league
            context['page_name'] = _('Schedule')      
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all().order_by('date')
        if self.kwargs.get('player'):
            player_pk = Player.objects.get(slug=self.kwargs.get('player')).pk
            qs = self.model.objects.filter(Q(white=player_pk) | Q(black=player_pk)).order_by('date')
        if self.kwargs.get('league') and self.kwargs.get('player'):
            league = League.objects.get(slug=self.kwargs['league'])
            league_pk = league.pk
            league_name = league.name
            player_pk = Player.objects.get(slug=self.kwargs.get('player')).pk
            qs = self.model.objects.filter(Q(home_team=player_pk) | Q(black=player_pk), league = league_pk ).order_by('-date')
        return qs



# Create your views here.

def player(request, player_id):
    query = request.GET.get('search')
    player = get_object_or_404(Player, id=player_id)
    games = {}
    for season in Season.objects.all():
        games[season] = {}
        for league in season.league_set.all():
            league_pk = league.pk
            games[season][league]  = Schedule.objects.filter(Q(white=player_id) | Q(black=player_id), league = league_pk).order_by('-date')
    return render(request, 'games.html', {'player': player, 'games': games})

def game(request, game_id):
    f = get_object_or_404(Schedule, id=game_id)
    return render(request, 'game.html', {'game': f})

def index(request):
    return render(request, 'league.html',{'leagues': League.objects.all()})