from django import forms
from django.contrib.admin import widgets
from .models import Player

class RoundForm(forms.Form):
    datetime = forms.DateTimeField(label='Date for Next Round', widget = widgets.AdminSplitDateTime, )
    last_round = forms.BooleanField(label='Last Round', initial = False, required = False)
    byes    = forms.ModelMultipleChoiceField( required = False, label = 'Byes', queryset = Player.objects.all() )

class LichessArenaForm(forms.Form):
    lichess_arena_id = forms.CharField(label='Lichess Arena ID', max_length=100)
class LichessSwissForm(forms.Form):
    lichess_swiss_id = forms.CharField(label='Lichess Swiss ID', max_length=100)
class LichessGameForm(forms.Form):
    lichess_game_id = forms.CharField(label='Lichess Game ID', max_length=100)