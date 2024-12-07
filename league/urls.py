from django.urls import re_path

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
    re_path(r"^season$", season, name="season"),
    re_path(r"^trophycabinet$", trophycabinet, name="trophycabinet"),
    re_path(r"^season/(?P<season_slug>[-\w]+)$", season, name="season"),
    re_path(r"^team_squads/(?P<season_slug>[-\w]+)$", team_squads, name="team_squads"),
    re_path(r"^team_fixtures/(?P<season_slug>[-\w]+)$", team_fixtures, name="team_fixtures"),
    re_path(r"^members/(?P<season>[-\w]+)$", members, name="members"),
    re_path(r"^team_squads$", team_squads, name="team_squads"),
    re_path(r"^team_fixtures$", team_fixtures, name="team_fixtures"),
    re_path(r"^members$", members, name="members"),
    re_path(r"^tournament/(?P<league>[-\w]+)$", fixtures, name="tournament"),
    re_path(r"^league/(?P<league>[-\w]+)$", fixtures, name="league"),
    re_path(r"^game/(?P<game_id>[0-9]+)$", game, name="game"),
    re_path(r"^player/(?P<player_id>[0-9]+)/league=(?P<league>[-\w]+)$", player, name="player"),
    re_path(r"^player/(?P<player_id>[0-9]+)/season=(?P<season>[-\w]+)$", player, name="player"),
    re_path(r"^player/(?P<player_id>[0-9]+)[/]$", player, name="player"),
    re_path(r"^committee$", committee, name="committee"),
    re_path(r"^committee/(?P<season>[-\w]+)$", committee, name="committee"),
    re_path(
        r"^export_league_pdf/(?P<league>[-\w]+)$",
        export_league_pdf,
        name="export_league_pdf",
    ),
    re_path(
        r"^export_crosstable_pdf/(?P<league>[-\w]+)$",
        export_crosstable_pdf,
        name="export_crosstable_pdf",
    ),
]
