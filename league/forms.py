from django import forms
from django.contrib.admin import widgets
from .models import Player, Schedule, League, Season
from datetime import datetime, timedelta
from django.db.models import Q

from calendar import monthrange
from django.contrib.admin.widgets import FilteredSelectMultiple

class RoundForm(forms.Form):
    datetime = forms.DateTimeField(label='Date for Next Round', widget = widgets.AdminSplitDateTime, )
    last_round = forms.BooleanField(label='Last Round', initial = False, required = False)
    byes    = forms.ModelMultipleChoiceField( required = False, label = 'Byes', queryset = Player.objects.all() )
class RoundRobinForm(forms.Form):
    datetime = forms.DateTimeField(label='Date for Round Robin', widget = widgets.AdminSplitDateTime, )

class LichessArenaForm(forms.Form):
    lichess_arena_id = forms.CharField(label='Lichess Arena ID', max_length=100)
class LichessSwissForm(forms.Form):
    lichess_swiss_id = forms.CharField(label='Lichess Swiss ID', max_length=100)
class LichessGameForm(forms.Form):
    lichess_game_id = forms.CharField(label='Lichess Game ID', max_length=100)
class PrintRoundForm(forms.Form):
    round_no = forms.ChoiceField(label="Round No.", choices = [0,1,2])

from django.forms import modelformset_factory

class ClubNightForm(forms.Form):
    # initialise with the last club night which should be a monday or thursday at 7.30 pm
    monday = datetime.today() - timedelta(days = datetime.today().weekday() % 7)
    thursday = datetime.today() - timedelta(days = (datetime.today().weekday() - 3) % 7)
    last = monday.replace(hour = 19, minute = 30, second = 0)
    if thursday > monday: last = thursday.replace(hour = 19, minute = 30, second = 0)
    datetime = forms.DateTimeField(label='Date of Club Night', widget = widgets.AdminSplitDateTime, initial = last)

class ExportGamesForm(forms.Form):
    start    = forms.DateTimeField(label='Start', widget=widgets.AdminSplitDateTime)
    end      = forms.DateTimeField(label='End', widget=widgets.AdminSplitDateTime)
    leagues  = forms.ModelMultipleChoiceField(required=True, label='Leagues', queryset=League.objects.none(), widget=FilteredSelectMultiple('Leagues', False))
    games    = forms.ModelMultipleChoiceField(required=False, label='Extra Games', queryset=Schedule.objects.none())
    players_exclude       = forms.ModelMultipleChoiceField(required=False, label='Players to exclude', queryset=Player.objects.none())
    ecf_code              = forms.CharField(required=False)
    event_name            = forms.CharField(required=False)
    results_officer       = forms.CharField(required=False)
    results_officer_address = forms.CharField(required=False)
    treasurer             = forms.CharField(required=False)
    treasurer_address     = forms.CharField(required=False)
    minutes               = forms.IntegerField(initial=90)
    start_date            = forms.DateField()
    end_date              = forms.DateField()
    submission_index      = forms.IntegerField(initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        season = Season.objects.order_by('end').last()
        if not season:
            return

        now = datetime.today()
        year, month = now.year, now.month
        if now.day < 5:
            if month == 1:
                year, month = year - 1, 12
            else:
                month -= 1

        month_days = monthrange(year, month)

        self.fields['start'].initial = datetime.combine(season.start, datetime.min.time())
        self.fields['end'].initial   = datetime(year=year, month=month, day=month_days[1], hour=23, minute=59)
        self.fields['leagues'].queryset       = League.objects.filter(season=season)
        self.fields['games'].queryset         = Schedule.objects.filter(
            Q(league__season=season) | (
                Q(date__isnull=False) &
                Q(date__date__gte=season.start) &
                Q(date__date__lte=season.end)
            )
        ).order_by('date')
        self.fields['players_exclude'].queryset = season.players.order_by('surename', 'name')
        self.fields['ecf_code'].initial              = season.ecf_code
        self.fields['event_name'].initial            = season.event_name
        self.fields['results_officer'].initial       = season.results_officer
        self.fields['results_officer_address'].initial = season.results_officer_address
        self.fields['treasurer'].initial             = season.treasurer
        self.fields['treasurer_address'].initial     = season.treasurer_address
        self.fields['start_date'].initial            = season.start
        self.fields['end_date'].initial              = season.end
    



ScheduleModelFormset = modelformset_factory(
    Schedule,
    fields=('white', 'black', 'result', 'league' ),
    extra=1,
    #widgets={'name': forms.TextInput(attrs={
    #        'class': 'form-control',
    #        'placeholder': 'Enter Book Name here'
    #    })
    #}
)

from django_summernote.widgets import SummernoteWidget
class LeagueAdminForm(forms.ModelForm):

    class Meta:
        model = League
        fields = '__all__'
        exclude = ['players','updated_date']

        widgets = {
            'description': SummernoteWidget(),
        }


class LeagueAdminChangeForm(forms.ModelForm):
    class Meta:
        model = League
        fields = '__all__'
        exclude = []

        widgets = {
            'description': SummernoteWidget(),
        }

    def __init__(self, *args,**kwargs):
        super (forms.ModelForm,self ).__init__(*args,**kwargs) # populates the post
        if self.instance and self.instance.season:
            #https://stackoverflow.com/questions/62711963/how-to-use-django-queryset-union-in-modeladmin-formfield-for-manytomany
            queryset = self.instance.season.players.union(self.instance.season.extra_players.all())
            queryset = Player.objects.filter(id__in = [q.id for q in queryset]).order_by('surename')
            self.fields['players'].queryset = queryset


class LeagueAdminKnockoutForm(forms.ModelForm):
    class Meta:
        model = League
        fields = '__all__'
        exclude = []

        widgets = {
            'description': SummernoteWidget(),
        }

    def __init__(self, *args,**kwargs):
        super (forms.ModelForm,self ).__init__(*args,**kwargs) # populates the post
        if self.instance and self.instance.season:
            self.fields['players'].queryset = self.instance.season.players.order_by('surename')

class SeasonAdminForm(forms.ModelForm):

    class Meta:
        model = Season
        fields = '__all__'
        exclude = ['slug']


class SeasonAdminChangeForm(forms.ModelForm):

    class Meta:
        model = Season
        fields = '__all__'
        exclude = []




class SeasonAdminForm(forms.ModelForm):

    class Meta:
        model = Season
        fields = '__all__'
        exclude = ['slug']


class ScheduleKnockoutForm(forms.ModelForm):

    class Meta:
        model = Schedule
        fields = ('round','date','white','black','result')
        exclude = []


class ScheduleLeagueForm(forms.ModelForm):

    class Meta:
        model = Schedule
        fields = ('date','white','black','result')
        exclude = []



class SendEmailForm(forms.Form):
    subject = forms.CharField(max_length=200)
    msg = forms.CharField(widget=forms.Textarea)
    attachment = forms.FileField(required=False)