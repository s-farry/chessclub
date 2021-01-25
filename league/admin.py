from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from django.forms import TextInput, Textarea, IntegerField
from .models import League, Schedule, Standings, Player, Season, STANDINGS_ORDER
from .forms import LichessArenaForm, LichessSwissForm, LichessGameForm
from django.utils import timezone
from django.urls import resolve

from datetime import datetime
from .utils import get_arena_games, get_swiss_games, get_game


def get_parent_object_from_request(self, request):
    """
    Returns the parent object from the request or None.

    Note that this only works for Inlines, because the `parent_model`
    is not available in the regular admin.ModelAdmin as an attribute.
    """
    resolved = resolve(request.path_info)
    if resolved.args:
        return self.parent_model.objects.get(id=resolved.kwargs['object_id'])
    return None

def standings_save(instance):
        league = League.objects.get(pk=instance.pk)
        league.updated_date = datetime.now()
        league.save()
        for player in league.players.all():
            obj, created = Standings.objects.get_or_create(league = league, player = player)
        
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
        now = timezone.now()
        for standing in standings:
            points = 0
            wins = 0
            lost = 0
            draws = 0
            matches = 0
            form = ''
            player = standing.player
            player_schedule = Schedule.objects.filter(~Q(result=3) & (Q(white=player) | Q(black=player)), league = instance.pk, date__lte=now).order_by('-date')
            for i,match in enumerate(player_schedule):
                matches += 1
                if match.white == player:
                    if match.result == 1 :
                        if i < 5:
                            form = 'W' + form
                        wins += 1
                        points += instance.win_points
                    elif match.result == 2 :
                        lost += 1
                        if i < 5:
                            form = 'L' + form
                        points += instance.lost_points
                    else:
                        draws += 1
                        if i < 5:
                            form = 'D' + form
                        points += instance.draw_points

                if match.black == player:
                    if match.result == 2 :
                        if i < 5:
                            form = 'W' + form
                        wins += 1
                        points += instance.win_points
                    elif match.result == 1 :
                        if i < 5:
                            form = 'L' + form
                        lost += 1
                        points += instance.lost_points
                    else:
                        draws += 1
                        if i < 5:
                            form = 'D' + form
                        points += instance.draw_points

                standing.points = points
                standing.win = wins
                standing.lost = lost
                standing.draws = draws
                standing.matches = matches
                standing.form = form
                standing.save()
        standings_position_update(instance)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    fields = ('round','date','white','black','result')
    max_num=100
    formfield_overrides = {
        models.IntegerField: {'widget': TextInput(attrs={'style':'width: 20px;'})},
    }


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        league = League.objects.get(id=resolve(request.path_info).kwargs['object_id'])
        if league is not None:
            # for ease of adding in the django admin, make it so that only
            # the players in the league are visible
            players = league.players.all()
            # but... need this in case someone is not in the league but has
            # already played, maybe they should be added to the league automatically
            games = Schedule.objects.filter(league = league.pk)
            for g in games:
                if g.white not in players:
                    # must be an easier way of adding to query!
                    players |= Player.objects.filter(pk = g.white.pk)
                if g.black not in players:
                    players |= Player.objects.filter(pk = g.black.pk)
            kwargs["queryset"] = players
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class StandingsInline(admin.TabularInline):
    model = Standings

    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """
        resolved = resolve(request.path_info)
        if resolved.args:
            return self.parent_model.objects.get(pk=resolved.args[0])
        return None
    ordering = ('position', '-points')
    exclude = ('matches', 'win', 'lost', 'draws', 'score', 'score_lost')
    max_num=0
    actions = []
    readonly_fields = ('player',)
    fields = ('points', 'position')



from functools import update_wrapper
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

class LeagueAdmin(ModelAdmin):
    change_form_template = 'change_form.html'
    manage_view_template = 'manage_form.html'
    inlines = [
        #StandingsInline, 
        ScheduleInline,
    ]
    prepopulated_fields = {'slug': ('name', 'season',), }
    actions=['update_standings']
    def update_standings(self,request,queryset):
        for obj in queryset:
            standings_save(obj)
            standings_update(obj)
            self.message_user(request, "league standings updated")

    def save_model(self, request, obj, form, change):
        obj.save()
        form.save_m2m()
        standings_save(obj)
        standings_update(obj)

    
    def get_urls(self):
        from django.conf.urls import url
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urls = [url(r'^(.+)/manage/$', wrap(self.manage_view),name='%s_%s_manage' % info)]
        super_urls = super(LeagueAdmin, self).get_urls()

        return urls + super_urls
    
    def manage_view(self, request, id ):
        opts = League._meta
        arena_form = LichessArenaForm()
        swiss_form = LichessSwissForm()
        game_form = LichessGameForm()
        obj = League.objects.get(pk=id)
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
            for g,v in games.items():
                if len(Schedule.objects.filter(lichess=g)) > 0:
                    schedule = Schedule.objects.filter(lichess=g)[0]
                    if schedule.league != obj:
                        self.message_user(request,'Game between %s and %s is in %s, changing to %s'%(v['white'],v['black'],schedule.league,obj))
                        schedule.league = obj
                        schedule.save()
                        nchanges += 1
                    else :
                        self.message_user(request,'Game between %s and %s is already in the database'%(v['white'],v['black']))
                    continue
                white = Player.objects.filter(lichess=v['white'])
                black = Player.objects.filter(lichess=v['black'])
                if len(white) == 0:
                    self.message_user(request,'Player %s is not in the database, skipping game' %(v['white']))
                    continue
                if len(black) == 0:
                    self.message_user(request,'Player %s is not in the database, skipping game' %(v['black']))
                    continue
                if white[0] not in obj.players.all():
                    self.message_user(request, 'Warning: Player %s is in the database but not the league' %(v['white']))
                if black[0] not in obj.players.all():
                    self.message_user(request, 'Warning: Player %s is in the database but not the league' %(v['black']))
                schedule = Schedule(league=obj,lichess=g,white=white[0],black=black[0],date=v['date'],result=v['result'])
                if 'pgn' in v.keys():
                    schedule.pgn = v['pgn']
                schedule.save()
                ngames+=1
            if ngames + nchanges > 0 :
                standings_save(obj)
                standings_update(obj)

            self.message_user(request, 'added %i games to %s'%(ngames + nchanges,obj))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        # do cool management stuff here

        preserved_filters = self.get_preserved_filters(request)
        form_url = request.build_absolute_uri()
        form_url = request.META.get('PATH_INFO', None)

        form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

        context = {
            'title': 'Manage %s' % obj,
            'has_change_permission': self.has_change_permission(request, obj),
            'opts': opts,
            #'errors': form.errors,
            'app_label': opts.app_label,
            'original': obj,
            'form_url' : form_url,
            'arena_form' : arena_form,
            'swiss_form' : swiss_form,
            'game_form' : game_form
        }

        return render(request, self.manage_view_template, context)

'''
class LeagueAdmin(admin.ModelAdmin):
    inlines = [
        #StandingsInline, 
        ScheduleInline,
    ]
    prepopulated_fields = {'slug': ('name', 'season',), }
    actions=['update_standings']
    def update_standings(self,request,queryset):
        for obj in queryset:
            standings_save(obj)
            standings_update(obj)
            self.message_user(request, "league standings updated")

    def save_model(self, request, obj, form, change):
        obj.save()
        form.save_m2m()
        standings_save(obj)
        standings_update(obj)
'''

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surename')
    list_filter = ('name',)


class ScheduleAdmin(admin.ModelAdmin):
    list_filter = ('league',)

admin.site.register(League, LeagueAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Season)
    
# Register your models here.
