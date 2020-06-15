from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from django.forms import TextInput, Textarea, IntegerField
from .models import League, Schedule, Standings, Player, Season, STANDINGS_ORDER
from django.utils import timezone
from datetime import datetime




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
            player = standing.player
            player_schedule = Schedule.objects.filter(Q(white=player) | Q(black=player), league = instance.pk, date__lte=now )
            for match in player_schedule:
                matches += 1
                if match.white == player:
                    if match.result == 1 :
                        wins += 1
                        points += instance.win_points
                    elif match.result == 2 :
                        lost += 1
                        points += instance.lost_points
                    else:
                        draws += 1
                        points += instance.draw_points

                if match.black == player:
                    if match.result == 2 :
                        wins += 1
                        points += instance.win_points
                    elif match.result == 1 :
                        lost += 1
                        points += instance.lost_points
                    else:
                        draws += 1
                        points += instance.draw_points

                standing.points = points
                standing.win = wins
                standing.lost = lost
                standing.draws = draws
                standing.matches = matches
                standing.save()
        standings_position_update(instance)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    formfield_overrides = {
        models.IntegerField: {'widget': TextInput(attrs={'style':'width: 20px;'})},
    }

class StandingsInline(admin.TabularInline):
    model = Standings
    ordering = ('position', '-points')
    exclude = ('matches', 'win', 'lost', 'draws', 'score', 'score_lost')
    max_num=0
    actions = []
    readonly_fields = ('player',)
    fields = ('points', 'position')




class LeagueAdmin(admin.ModelAdmin):
    inlines = [
        StandingsInline, 
        #ScheduleInline,
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


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surename')
    list_filter = ('name',)
        

admin.site.register(League, LeagueAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Schedule)
admin.site.register(Season)
    
# Register your models here.
