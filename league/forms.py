from django import forms

class LichessArenaForm(forms.Form):
    lichess_arena_id = forms.CharField(label='Lichess Arena ID', max_length=100)
class LichessSwissForm(forms.Form):
    lichess_swiss_id = forms.CharField(label='Lichess Swiss ID', max_length=100)
class LichessGameForm(forms.Form):
    lichess_game_id = forms.CharField(label='Lichess Game ID', max_length=100)