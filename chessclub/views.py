from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, Season, Player, STANDINGS_ORDER
from content.models import news
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render

def index(request):
    return render(request, 'index.html',{'seasons': Season.objects.all(), 'news' : news.objects.order_by("-published_date")[:3]})