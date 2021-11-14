from django import forms
from django.contrib.admin import widgets
from .models import Player, Schedule, League
from datetime import datetime, timedelta
from calendar import monthrange

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
    now = datetime.today()
    year     = now.year
    month   = now.month
    if now.day < 10:
        if month == 1:
            year = year - 1
            month = 12
        else:
            month = month - 1

    month_days = monthrange(year, month)
    start = forms.DateTimeField(label='Start', widget = widgets.AdminSplitDateTime, initial = datetime(year=year, month = month, day = 1))
    end   = forms.DateTimeField(label='End', widget = widgets.AdminSplitDateTime, initial = datetime(year=year, month = month, day = month_days[1]))

    leagues    = forms.ModelMultipleChoiceField( required = True, label = 'Leagues', queryset = League.objects.all() )



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