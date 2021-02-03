from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from django.forms import TextInput, Textarea, IntegerField, CharField
from .models import League, Schedule, Standings, Player, Season, STANDINGS_ORDER, POINTS
from .forms import LichessArenaForm, LichessSwissForm, LichessGameForm, RoundForm
from django.utils import timezone
from django.urls import resolve
from django import forms

from datetime import datetime
from .utils import get_arena_games, get_swiss_games, get_game

from tinymce.widgets import TinyMCE

from swissdutch.dutch import DutchPairingEngine
from swissdutch.constants import FideTitle, Colour, FloatStatus
from swissdutch.player import Player as PairingPlayer
import random, operator

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


def get_next_round(round_no, engine, last_round):
    paired_players = engine.pair_round(round_no, tuple(last_round.values()))
    ivd = {v.pairing_no: k for k, v in last_round.items()}
    next_round = { ivd[pp.pairing_no].pk : pp for pp in paired_players }
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
    return pairs, id_pairs

def create_games_from_id_pairs(league, round_no, pairs, date):
    games = []
    for p in pairs:
        player = Player.objects.get(pk = p[0])
        opponent = Player.objects.get(pk = p[1])
        games += [ Schedule(league=league,round = round_no,white=player,black=opponent, date = date) ]
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

def test_swiss(league, nrounds):
    # this is a test which, for aims to see if keeping track of the rounds is the same as
    # creating from the database anew each round
    persistent_pairings = ()
    first_db_pairings = {}
    games_to_delete = []
    engine  = DutchPairingEngine(top_seed_colour_selection_fn = top_seed_colour_selection)
    #engine2 = DutchPairingEngine(top_seed_colour_selection_fn = top_seed_colour_selection)
    for i in range(nrounds):
        #print('-----------')
        last_round = get_last_round(league)
        if i == 0 :
            persistent_pairings = tuple([t for t in last_round.values()])
            first_db_pairings   = { p : v.pairing_no for p,v in last_round.items()  }
        new_pairings = tuple([t for t in last_round.values()])
        #assert(all([a in b for a, b in zip(persistent_pairings, new_pairings)]))
        #for a,b in zip(persistent_pairings, new_pairings):
        #    print(a.pairing_no, a.score,a._float_status, a.opponents,b.pairing_no,b.score,b.opponents, b._float_status)
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
        persistent_pairings = engine.pair_round(i+1, persistent_pairings)
        next_round = get_next_round(i+1, engine, last_round)
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
        games = create_games(league, i+1, next_round, datetime.now())
        games_to_delete += games
        for g in games:
            result = random.choice([0,1,2])
            g.result = result
            g.save()
            # the persistent pairing has not changed form initial pairing numbers
            white_pairing_no = first_db_pairings[g.white]
            black_pairing_no = first_db_pairings[g.black]
            for pp in persistent_pairings:
                if pp.pairing_no == white_pairing_no:
                    if result == 0 : pp._score += 1
                    elif result == 1 : pp._score += 2
                if pp.pairing_no == black_pairing_no:
                    if result == 0 : pp._score += 1
                    elif result == 2 : pp._score += 2
    for g in games_to_delete:
        g.delete()



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
            obj, created = Standings.objects.get_or_create(league = league, player = player, rating = player.rating)
        
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
            player_schedule = Schedule.objects.filter(~Q(result=3) & (Q(white=player) | Q(black=player)), league = instance.pk).order_by('-date')

            for i,match in enumerate(player_schedule):
                matches += 1
                if match.white == player:
                    if match.result == 1 :
                        if (instance.get_type_display() == "Swiss" and i < 20) or i < 5:
                            form = 'W' + form
                        wins += 1
                        points += instance.get_win_points_display()
                    elif match.result == 2 :
                        lost += 1
                        if (instance.get_type_display() == "Swiss" and i < 20) or i < 5:
                            form = 'L' + form
                        points += instance.get_lost_points_display()
                    else:
                        draws += 1
                        if (instance.get_type_display() == "Swiss" and i < 20) or i < 5:
                            form = 'D' + form
                        points += instance.get_draw_points_display()

                if match.black == player:
                    if match.result == 2 :
                        if (instance.get_type_display() == "Swiss" and i < 20) or i < 5:
                            form = 'W' + form
                        wins += 1
                        points += instance.get_win_points_display()
                    elif match.result == 1 :
                        if (instance.get_type_display() == "Swiss" and i < 20) or i < 5:
                            form = 'L' + form
                        lost += 1
                        points += instance.get_lost_points_display()
                    else:
                        draws += 1
                        if (instance.get_type_display() == "Swiss" and i < 20) or i < 5:
                            form = 'D' + form
                        points += instance.get_draw_points_display()

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
        if 'object_id' in kwargs:
            league = League.objects.get(id=resolve(request.path_info).kwargs['object_id'])
            if league is not None:
                # for ease of adding in the django admin, make it so that only
                # the players in the league are visible
                players = [p.pk for p in league.players.all()]
                # but... need this in case someone is not in the league but has
                # already played, maybe they should be added to the league automatically
                games = Schedule.objects.filter(league = league.pk)
                for g in games:
                    if g.white.pk not in players:
                        players += [ g.white.pk ]
                    if g.black not in players:
                        players += [ g.black.pk]
                kwargs["queryset"] = Player.objects.filter(pk__in = players)
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


class LeagueAdminForm(forms.ModelForm):

    class Meta:
        model = League
        fields = '__all__'
        exclude = []
        
        widgets = {
            'description': TinyMCE(attrs = {'rows' : '30', 'cols' : '100', 'content_style' : "color:#FFFF00", 'body_class': 'review', 'body_id': 'review',})
        }

class LeagueAdmin(ModelAdmin):
    change_form_template = 'change_form.html'
    manage_view_template = 'manage_form.html'
    create_round_template = 'create_round.html'
    form = LeagueAdminForm
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
        urls += [url(r'^(.+)/create_round/$', wrap(self.create_round_view),name='%s_%s_create_round' % info)]

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


    def create_round_view(self, request, id ):
        opts = League._meta
        obj = League.objects.get(pk=id)
        form = RoundForm()

        preserved_filters = self.get_preserved_filters(request)
        form_url = request.build_absolute_uri()
        form_url = request.META.get('PATH_INFO', None)

        form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

        context = {
                'title': 'Create Round for %s' % obj,
                'has_change_permission': self.has_change_permission(request, obj),
                'opts': opts,
                'form' : form,
                #'errors': form.errors,
                'app_label': opts.app_label,
                'original': obj,
                'form_url' : form_url,
        }
        #test_swiss(obj,5)
        if request.POST and request.POST.get('create_swiss_games'):
            # rond has been paired and confirmed, make the games
            id_pairs = request.session.get('pairs')
            date = request.POST.get('date')
            time = request.POST.get('time')
            round_date = datetime.strptime('%s %s'%(date,time), '%Y-%m-%d %H:%M:%S')
            print('round_date',round_date)
            roundno = request.POST.get('round')
            games = create_games_from_id_pairs(obj, roundno, id_pairs, round_date)
            for g in games:
                self.message_user(request, '%s will play %s'%(g.white, g.black))
                g.save()


        elif request.POST and request.POST.get('create_swiss_round') is not None:
            # here we've been asked to create a round

            # check if it's legal (more checks should be added)
            unfinished_games = Schedule.objects.filter(league=obj,result=3)
            if len(unfinished_games) > 0 :
                self.message_user(request, "There are %i unfinished games, can't create new round!"%(len(unfinished_games)))
            else:
                # create it and send it back for confirmation
                date = request.POST.get('datetime_0')
                time = request.POST.get('datetime_1')
                round_date = datetime.strptime('%s %s'%(date,time), '%Y-%m-%d %H:%M:%S')
                rounds = obj.get_rounds()
                standings = Standings.objects.filter(league = obj)
                next_round_no = 1
                if len(rounds) > 0 : next_round_no = rounds[-1] + 1
                engine  = DutchPairingEngine()
                last_round = get_last_round(obj)
                next_round = get_next_round(next_round_no, engine, last_round)
                pairs, id_pairs = get_pairs(next_round)
                context['pairs'] = pairs
                context['round'] = next_round_no
                context['date'] = date
                context['time'] = time
                request.session['pairs'] = id_pairs

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        return render(request, self.create_round_template, context)


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
