from django.conf.urls import url

from .views import (
    StandingsFull,
    ScheduleFull,
    game,
    index,
    player,
    fixtures,
    season,
    leagues,
    members,
    export_league_pdf,
    export_crosstable_pdf,
    trophycabinet,
    team_fixtures,
    team_squads,
)

urlpatterns = [
    url(r"^tournaments$", leagues, name="tournaments"),
    url(r"^tournament$", leagues, name="tournament"),
    url(r"^tournaments/(?P<season_slug>[-\w]+)$", leagues, name="tournaments"),
    url(r"^season$", season, name="season"),
    url(r"^trophycabinet$", trophycabinet, name="trophycabinet"),
    url(r"^season/(?P<season_slug>[-\w]+)$", season, name="season"),
    url(r"^team_squads/(?P<season_slug>[-\w]+)$", team_squads, name="team_squads"),
    url(r"^team_fixtures/(?P<season_slug>[-\w]+)$", team_fixtures, name="team_fixtures"),
    url(r"^members/(?P<season>[-\w]+)$", members, name="members"),
    url(r"^team_squads$", team_squads, name="team_squads"),
    url(r"^team_fixtures$", team_fixtures, name="team_fixtures"),
    url(r"^members$", members, name="members"),
    url(r"^tournament/(?P<league>[-\w]+)$", fixtures, name="tournament"),
    url(r"^league/(?P<league>[-\w]+)$", fixtures, name="league"),
    url(r"^game/(?P<game_id>[0-9]+)$", game, name="game"),
    url(r"^player/(?P<player_id>[0-9]+)/league=(?P<league>[-\w]+)$", player, name="player"),
    url(r"^player/(?P<player_id>[0-9]+)/season=(?P<season>[-\w]+)$", player, name="player"),
    url(r"^player/(?P<player_id>[0-9]+)[/]$", player, name="player"),
    url(
        r"^export_league_pdf/(?P<league>[-\w]+)$",
        export_league_pdf,
        name="export_league_pdf",
    ),
    url(
        r"^export_crosstable_pdf/(?P<league>[-\w]+)$",
        export_crosstable_pdf,
        name="export_crosstable_pdf",
    ),
]
