from django import forms
from django.contrib.admin import widgets
import datetime
from .models import simul

class LichessEventForm(forms.Form):
    name=forms.CharField(label="Tournament Name", initial="Wallasey Blitz", max_length=100)
    today = datetime.datetime.now()
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    next_monday = next_monday.replace(hour=19,minute=30,second=0)
    datetime = forms.DateTimeField(label='Date of Tournament', widget = widgets.AdminSplitDateTime, initial = next_monday )
    time = forms.IntegerField(initial = 5, label="Starting Time")
    increment = forms.IntegerField(initial = 3, label="Incement")
    duration = forms.IntegerField(initial = 90, label="Duration")

class SimulForm(forms.ModelForm):
    class Meta:
        model = simul
        exclude = []