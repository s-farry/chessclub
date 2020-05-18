from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, Season, Player, STANDINGS_ORDER
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render

class StandingsFull(ListView):
    template_name = 'standings.html'
    model = Standings
    context_object_name = 'standings'

    def get_context_data(self, **kwargs):
        context = super(StandingsFull, self).get_context_data(**kwargs)
        
        season_name = ''
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
            season_pk = season.pk
            season_name = ": {} {}".format(season.name, season.league)
        
        context['table_name'] = season_name
        context['slug'] = self.kwargs.get('season')
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
            season_pk = season.pk
            season_name = season.name
            order = STANDINGS_ORDER[season.standings_order][1]
            qs = self.model.objects.filter(season=season_pk).order_by(*order)
        return qs


class ScheduleFull(ListView):
    template_name = 'schedule.html'
    model = Schedule
    context_object_name = 'schedule'

    def get_context_data(self, **kwargs):
        context = super(ScheduleFull, self).get_context_data(**kwargs)
        
        season_name = ''
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
            season_pk = season.pk
            season_name = ": {} {}".format(season.name, season.league)
            context['page_name'] = _('Schedule')
            context['season'] = season_name
            context['slug'] = self.kwargs.get('season')
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
            season_pk = season.pk
            season_name = season.name
            qs = self.model.objects.filter(season=season_pk).order_by('-date')
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
        
        if self.kwargs.get('season'):
            season = Season.objects.get(slug=self.kwargs['season'])
            context['season'] = season
            context['page_name'] = _('Schedule')      
        
        return context


    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all().order_by('date')
        if self.kwargs.get('player'):
            player_pk = Player.objects.get(slug=self.kwargs.get('player')).pk
            qs = self.model.objects.filter(Q(white=player_pk) | Q(black=player_pk)).order_by('date')
        if self.kwargs.get('season') and self.kwargs.get('player'):
            season = Season.objects.get(slug=self.kwargs['season'])
            season_pk = season.pk
            season_name = season.name
            player_pk = Team.objects.get(slug=self.kwargs.get('player')).pk
            qs = self.model.objects.filter(Q(home_team=player_pk) | Q(black=player_pk), season = season_pk ).order_by('-date')
        return qs



# Create your views here.

def player(request, player_id):
    query = request.GET.get('search')
    player = get_object_or_404(Player, id=player_id)
    games  = Schedule.objects.filter(Q(white=player_id) | Q(black=player_id)).order_by('-date')
    return render(request, 'games.html', {'player': player, 'games': games})

def game(request, game_id):
    f = get_object_or_404(Schedule, id=game_id)
    return render(request, 'game.html', {'game': f})

def index(request):
    return render(request, 'league.html',{'seasons': Season.objects.all()})