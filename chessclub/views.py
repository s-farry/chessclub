from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, League, Player, STANDINGS_ORDER
from content.models import news, event, Puzzle
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render
from datetime import datetime

def index(request):
    news_objects   = news.objects.order_by("-published_date")[:3]
    events_objects = event.objects.filter( Q(date__gte = datetime.now()) ).order_by('date')[:5]
    puzzles = Puzzle.objects.filter(date=datetime.now().date() )
    return render(request, 'index.html',{'leagues': League.objects.all(), 'news' : news_objects, 'events' : events_objects, 'puzzles' : puzzles } )