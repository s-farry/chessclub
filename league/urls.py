from django.conf.urls import url

from .views import StandingsFull, ScheduleFull, TeamRoster, game, index, player, fixtures, season, leagues, export_league_pdf

urlpatterns = [
    url(r'^tournaments$', leagues, name='tournaments'),
    url(r'^tournaments/(?P<season_slug>[-\w]+)$', leagues, name='tournaments'),
    url(r'^season$', season, name='season' ),
    url(r'^season/(?P<season_slug>[-\w]+)$', season, name='season' ),
    url(r'^members$', TeamRoster.as_view(), name='members' ),
    url(r'^members/(?P<season>[-\w]+)$', TeamRoster.as_view(), name='members' ),
    url(r'^tournament/(?P<league>[-\w]+)$', fixtures, name='tournament' ),
    url(r'^league/(?P<league>[-\w]+)$', fixtures, name='league' ),
    url(r'^game/(?P<game_id>[0-9]+)$', game, name='game'),
    url(r'^player/(?P<player_id>[0-9]+)/(?P<league>[-\w]+)$', player, name='player'),
    url(r'^player/(?P<player_id>[0-9]+)$', player, name='player'),
    url(r'^export_league_pdf/(?P<league>[-\w]+)$', export_league_pdf, name='export_league_pdf')
]
