from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, League, Player, STANDINGS_ORDER, TeamFixture
from content.models import news, event, Puzzle, page
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render
from datetime import datetime


def index(request):
    news_objects = news.objects.order_by("-published_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=datetime.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=datetime.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=datetime.now().date())

    about = htmlobject.objects.filter(title='About Us')[0]

    return render(
        request,
        "index.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures" : team_fixtures,
            "about" : about
        },
    )

def preview(request):
    news_objects = news.objects.order_by("-created_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=datetime.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=datetime.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=datetime.now().date())
    return render(
        request,
        "index.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures" : team_fixtures,
        },
    )

def page_not_found(request, *args, **kwargs):
    return render(request, "404.html", *args, **kwargs)


def server_error(request, *args, **kwargs):
    return render(request, "500.html", *args, **kwargs)
