from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from league.models import Schedule, Standings, League, Player, STANDINGS_ORDER, TeamFixture, LMSTeamFixture, Season
from content.models import news, event, Puzzle, page, snippet
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, render
from django.utils import timezone


def index(request):
    news_objects = news.objects.order_by("-published_date")[:3]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())

    about = snippet.objects.filter(title='About Us')[0]

    current_season = Season.objects.order_by('end').last()
    member_count = current_season.players.count() if current_season else 0
    league_count = League.objects.filter(season=current_season).count() if current_season else 0

    _next_lms = LMSTeamFixture.objects.filter(
        Q(date__gte=timezone.now()),
        Q(home_team__icontains='wallasey') | Q(away_team__icontains='wallasey')
    ).order_by('date').first()
    next_lms_fixtures = list(LMSTeamFixture.objects.filter(
        Q(home_team__icontains='wallasey') | Q(away_team__icontains='wallasey'),
        date__date=_next_lms.date.date()
    ).order_by('date')) if _next_lms else []

    _next_fix = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by('date').first()
    next_fixtures = list(TeamFixture.objects.filter(
        date__date=_next_fix.date.date()
    ).order_by('date')) if _next_fix else []

    # Featured league standings (top 6)
    featured_league = current_season.featured_league if current_season else None
    featured_standings = []
    if featured_league:
        order = STANDINGS_ORDER[featured_league.standings_order][1]
        featured_standings = list(
            Standings.objects.filter(league=featured_league).order_by(*order)[:6]
        )

    return render(
        request,
        "index.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures": team_fixtures,
            "about": about,
            "next_lms_fixtures": next_lms_fixtures,
            "next_fixtures": next_fixtures,
            "member_count": member_count,
            "league_count": league_count,
            "featured_league": featured_league,
            "featured_standings": featured_standings,
        },
    )


def index_test(request):
    news_objects = news.objects.order_by("-published_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())

    about = snippet.objects.filter(title='About Us')[0]

    return render(
        request,
        "index2.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures" : team_fixtures,
            "about" : about
        },
    )

def index_test2(request):
    news_objects = news.objects.order_by("-published_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())

    about = snippet.objects.filter(title='About Us')[0]

    return render(
        request,
        "index3.html",
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
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())
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

def design_test(request):
    return render(request, "design_test.html")

def page_not_found(request, *args, **kwargs):
    return render(request, "404.html", *args, **kwargs)


def server_error(request, *args, **kwargs):
    return render(request, "500.html", *args, **kwargs)
