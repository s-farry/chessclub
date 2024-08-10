from django.conf.urls import url

from .views import (
    StandingsFull,
    ScheduleFull,
    game,
    player,
    fixtures,
    season,
    members,
    export_league_pdf,
    export_crosstable_pdf,
    trophycabinet,
    team_fixtures,
    team_squads,
    committee
)

urlpatterns = [
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
    url(r"^committee$", committee, name="committee"),
    url(r"^committee/(?P<season>[-\w]+)$", committee, name="committee"),
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
