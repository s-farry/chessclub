from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from django.forms import TextInput, Textarea, IntegerField, CharField
from .models import League, Schedule, Standings, Player, Season, Team, TeamPlayer, TeamFixture, STANDINGS_ORDER, POINTS, PGN
from .forms import LeagueAdminForm, LeagueAdminChangeForm, SeasonAdminForm, SeasonAdminChangeForm
from django.utils import timezone
from django.urls import resolve, reverse
from django.utils.safestring import mark_safe
from django import forms
from datetime import datetime
from .utils import standings_save, standings_update
from django.contrib.admin import DateFieldListFilter, SimpleListFilter

from django.template.defaultfilters import slugify

from django_reverse_admin import ReverseModelAdmin


from django.forms import BaseInlineFormSet
import requests

import utils

from .views import create_round_robin_view, create_round_view, manage_league_view, manage_schedule_view, export_league_pdf, export_crosstable_pdf, add_club_night_view, export_games_view, make_table, make_crosstable

class LimitModelFormset(BaseInlineFormSet):
    """ Base Inline formset to limit inline Model query results. """
    def __init__(self, *args, **kwargs):
        super(LimitModelFormset, self).__init__(*args, **kwargs)
        _kwargs = {self.fk.name: kwargs['instance']}
        self.queryset = kwargs['queryset'].filter(**_kwargs).order_by('-id')[:20]

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


class ScheduleInline(admin.TabularInline):
    model = Schedule
    fields = ('round','date','white','black','result')
    formfield_overrides = {
        models.IntegerField: {'widget': TextInput(attrs={'style':'width: 20px;'})},
    }
    show_change_link = True
    formset = LimitModelFormset
    max_num = 25
    extra = 5

    def get_extra (self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            # Don't add any extra forms if the related object already exists.
            return 0
        return self.extra

    
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

    def save_related(self, request, form, formset, change):
        print("saving related 2")
        instances = formset.save(commit=False)
        for instance in instances:
            if not change and (not instance.white_rating or not instance.black_rating):
                if instance.white:
                    instance.white_rating = instance.white.rating
                if instance.black:
                  instance.black_rating = instance.black.rating
            # Do something with `instance`
            instance.save()
        formset.save_m2m()

class TeamFixtureInline(admin.TabularInline):
    model = TeamFixture


class TeamPlayerInline(admin.TabularInline):
    model = TeamPlayer

class PgnInline(admin.TabularInline):
    model = PGN
    max_num = 1
    extra = 1

class StandingsInline(admin.TabularInline):
    model = Standings
    extra = 0

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
    exclude = ('score', 'score_lost')
    #max_num=3
    actions = []
    #readonly_fields = ('player',)
    fields = ('position','matches','win','draws','lost','points')



from functools import update_wrapper
from django.contrib import admin
from django.contrib.admin import ModelAdmin


from matplotlib.backends.backend_pdf import PdfPages
from django.http import HttpResponse
from io import BytesIO

class SeasonLeagueFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'season'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'season'


    def choices(self, changelist):
        choices = super().choices(changelist)
        next(choices)
        return choices
    
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        seasons = Season.objects.all().order_by('end')
        lookup_items = [
            #('all', 'All' ),
        ]
        if len(seasons) > 0:
            lookup_items += [
                (None, seasons.last() )
            ]
            lookup_items += [
                (s.slug, s) for s in Season.objects.all().order_by('-end') if s != seasons.last()
            ]

        return lookup_items

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.

        seasons = Season.objects.all().order_by('end')
        if self.value():
            season = Season.objects.filter(slug=self.value())[0]
            return queryset.filter(id__in=[p.id for p in League.objects.filter(season=season)])
        elif len(seasons) > 0:
            return queryset.filter(id__in=[p.id for p in League.objects.filter(season=seasons.last())])
        else:
            return queryset
    



class LeagueAdmin(ModelAdmin):
    change_form_template = 'change_form.html'
    manage_view_template = 'manage_form.html'
    create_round_template = 'create_round.html'
    create_round_robin_template = 'create_round_robin.html'
    filter_horizontal = ('players',)

    list_filter = (SeasonLeagueFilter,)

    form = LeagueAdminForm
    inlines = [
        StandingsInline, 
        ScheduleInline,
    ]
    change_form = LeagueAdminChangeForm

    def link(self, obj):
        url = reverse('league',args = {obj.slug})
        return mark_safe("<a href='%s' target='blank'>Open</a>" % url)

    #prepopulated_fields = {'slug': ('name', 'season_name',), }
    actions=['update_standings', 'make_pdf', 'make_crosstable', 'update_ratings', 'update_historical_ratings']
    list_display = ('name','link')
    def update_standings(self,request,queryset):
        for obj in queryset:
            standings_save(self, request, obj)
            standings_update(self, request, obj)
            self.message_user(request, "Standings for %s updated"%(obj))

    def update_ratings(self,request,queryset):
        for obj in queryset:
            standings = Standings.objects.filter(league=obj)
            for s in standings:
                if s.player and s.player.rating:
                    s.rating = s.player.rating
                    s.save()
            self.message_user(request, "Ratings of players in league updated")


    def update_historical_ratings(self, request, queryset):
        for obj in queryset:
            ratings_date = obj.season.end
            standings = Standings.objects.filter(league=obj)
            for s in standings:
                p = s.player
                if p.ecf == None:
                    self.message_user(request, '%s has no ECF code currently'%(p))
                    continue
                url = 'https://www.ecfrating.org.uk/v2/new/api.php?v2/ratings/Standard/%s/%s'%(p.ecf, ratings_date)
                grade = requests.get(url)
                if grade:
                    grade = grade.json()
                    curr_rating = s.rating if s.rating else 0
                    self.message_user(request, '%s rating updated from %i to %i'%(p, curr_rating, grade['revised_rating']))
                    s.rating = grade['revised_rating']
                    s.save()
                else:
                    s.rating=None
                    s.save()
                print('Rating not found for %s for ecf code %s'%(p,p.ecf))


    def make_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        filename = 'league_tables'
        response['Content-Disposition'] = 'attachement; filename={0}.pdf'.format(filename)
        buffer = BytesIO()
        with PdfPages(buffer) as pdf:
            for obj in queryset:
                fig = make_table(obj)
                pdf.savefig()

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response

    def make_crosstable(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        filename = 'league_crosstables'
        response['Content-Disposition'] = 'attachement; filename={0}.pdf'.format(filename)
        buffer = BytesIO()
        with PdfPages(buffer) as pdf:
            for obj in queryset:
                fig = make_crosstable(obj)
                pdf.savefig()

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response


    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.slug = slugify('{}'.format('%s-%s'%(obj.name, obj.season.slug)))
        #obj.save()
        super().save_model(request, obj, form, change)
        form.save_m2m()
        # create standings first time
        if not change:
            standings_save(self, request, obj)
            #standings_update(obj)

    
    def get_urls(self):
        from django.conf.urls import url
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, self, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urls = [url(r'^(.+)/manage/$', wrap(manage_league_view),name='%s_%s_manage' % info)]
        urls += [url(r'^(.+)/create_round/$', wrap(create_round_view),
        name='%s_%s_create_round' % info)]
        urls += [url(r'^(.+)/create_round_robin/$', wrap(create_round_robin_view),
        name='%s_%s_create_round_robin' % info)]
        urls += [url(r'^(.+)/download_pdf/$', wrap(export_league_pdf),
        name='%s_%s_download_pdf' % info)]
        urls += [url(r'^(.+)/download_crosstable/$', wrap(export_crosstable_pdf),
        name='%s_%s_download_crosstable' % info)]

        
        super_urls = super(LeagueAdmin, self).get_urls()
        return urls + super_urls

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during foo creation
        """
        defaults = {}
        if obj is not None:
            defaults['form'] = self.change_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
    
    def save_related(self, request, form, formsets, change):
        for formset in formsets:
            if formset.model == Schedule:
                instances = formset.save(commit=False)
                for instance in instances:
                    if instance.pk: continue

                    if (not instance.white_rating or not instance.black_rating):
                        if instance.white:
                            instance.white_rating = instance.white.rating
                        if instance.black:
                            instance.black_rating = instance.black.rating
                    instance.save()

        super(LeagueAdmin, self).save_related(request, form, formsets, change)

class SeasonPlayersFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Season'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'season'

    def choices(self, changelist):
        choices = super().choices(changelist)
        next(choices)
        return choices
    
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        seasons = [
            (s.slug, s) for s in Season.objects.all().order_by('-end')
        ]
        return seasons

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        seasons = Season.objects.all().order_by('-end')
        # Compare the requested value
        # to decide how to filter the queryset.
        if self.value():
            return queryset.filter(id__in=[p.id for p in Season.objects.filter(slug=self.value())[0].players.all()])
        elif len(seasons) > 0:
            return queryset.filter(id__in=[p.id for p in seasons[0].players.all()])
        else:
            return queryset

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surename')
    list_filter = (SeasonPlayersFilter,)
    ordering = ('surename',)
    actions = ['update_ratings']
    def update_ratings(self, request, queryset):
        for p in queryset:
            if p.ecf == None:
                self.message_user(request, '%s has no ECF code currently'%(p))
                continue
            url = 'https://www.ecfrating.org.uk/v2/new/api.php?v2/ratings/Standard/%s/%s'%(p.ecf, datetime.today().date())
            grade = requests.get(url)
            if grade:
                grade = grade.json()
                curr_rating = p.rating if p.rating else 0
                self.message_user(request, '%s rating updated from %i to %i'%(p, curr_rating, grade['revised_rating']))
                p.rating = grade['revised_rating']
                p.save()
            print('Rating not found for %s for ecf code %s'%(p,p.ecf))



class LeagueGamesFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'League'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'season'
   
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        seasons = Season.objects.all()
        leagues = []
        if len(seasons) > 0:
            leagues += [
               (l.slug, l) for l in League.objects.filter(season=seasons.last())
            ]
            
        return leagues

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.
        if self.value():
            print(self.value())
            return queryset.filter(league__slug=self.value())
        else:
            return queryset



class HistoricalLeagueGamesFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Older League'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'season'
   
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        seasons = Season.objects.all()
        leagues = []
        if len(seasons) > 0:
            leagues += [
               (l.slug, l) for l in League.objects.exclude(season=seasons.last())
            ]
        return leagues

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.
        if self.value():
            print(self.value())
            return queryset.filter(league__slug=self.value())
        else:
            return queryset




class ScheduleAdmin(ReverseModelAdmin):
    change_list_template = 'change_game_list.html'
    change_form_template = 'change_game_form.html'
    manage_view_template = 'manage_game_form.html'
    add_clubnight_template = 'add_club_night.html'
    export_games_template = 'export_games.html'
    list_filter = (LeagueGamesFilter,('date', DateFieldListFilter), HistoricalLeagueGamesFilter )
    inline_reverse = ['pgn']

    inlines = [
        PgnInline,
    ]
    def get_urls(self):
        from django.conf.urls import url
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, self, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        urls = [url(r'^addclubnight/', wrap(add_club_night_view), name='%s_%s_addclubnight' 
        % info)]
        urls += [url(r'^exportgames/', wrap(export_games_view),name='%s_%s_exportgames' 
        % info)]

        super_urls = super(ScheduleAdmin, self).get_urls()
        return urls + super_urls

    def save_model(self, request, obj, form, change):
        print("saving schedule admin")
        super(ScheduleAdmin, self).save_model(request, obj, form, change)
        if not change and (not obj.white_rating or not obj.black_rating):
            if obj.white:
                obj.white_rating = obj.white.rating
            if obj.black:
                obj.black_rating = obj.black.rating
            obj.save()


    def save_formset(self, request, form, formset, change):
        print("saving formset")
        instances = formset.save(commit=False)
        for instance in instances:
            if not change and (not instance.white_rating or not instance.black_rating):
                if instance.white:
                    instance.white_rating = instance.white.rating
                if instance.black:
                  instance.black_rating = instance.black.rating
            # Do something with `instance`
            instance.save()
        formset.save_m2m()

    def save_related(self, request, form, formset, change):
        print("saving related 1")
        instances = formset.save(commit=False)
        for instance in instances:
            if not change and (not instance.white_rating or not instance.black_rating):
                if instance.white:
                    instance.white_rating = instance.white.rating
                if instance.black:
                  instance.black_rating = instance.black.rating
            # Do something with `instance`
            instance.save()
        formset.save_m2m()


    def update_ratings(self,request,queryset):
        for obj in queryset:
            white_rating = obj.white_rating if obj.white_rating else 0
            black_rating = obj.black_rating if obj.black_rating else 0
            new_white_rating = white_rating
            new_black_rating = black_rating
            if obj.white and obj.white.rating:
                new_white_rating = obj.white.rating
                obj.white_rating = obj.white.rating
            if obj.black and obj.black.rating:
                new_black_rating = obj.black.rating
                obj.black_rating = obj.black.rating
            obj.save()

            self.message_user(request, "Ratings in %s %s %s updated from (%i,%i) to (%i,%i)"%(obj.white, obj.get_result_display(), obj.black, white_rating, black_rating, new_white_rating, new_black_rating))
    actions=['update_ratings']

class SeasonAdmin(admin.ModelAdmin):
    filter_horizontal = ('players',)
    form = SeasonAdminForm
    change_form = SeasonAdminChangeForm

    def save_model(self, request, obj, form, change):
        if not change:
            y1 = obj.start.year
            y2 = obj.end.year
            if y1 == y2:
                obj.slug = obj.start.strftime('%Y')
            else:
                obj.slug = '%s-%s'%(obj.start.strftime('%y'), obj.end.strftime('%y'))
        super().save_model(request, obj, form, change)

        form.save_m2m()

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during creation
        """
        defaults = {}
        if obj is not None:
            defaults['form'] = self.change_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    

class TeamAdmin(admin.ModelAdmin):

    inlines = [
        TeamFixtureInline,
        TeamPlayerInline,
    ]



admin.site.register(League, LeagueAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Season, SeasonAdmin)
#admin.site.register(Team, TeamAdmin)
#admin.site.register(Standings)


# Register your models here.
