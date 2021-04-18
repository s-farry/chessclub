from django.conf.urls import url

from .views import StandingsFull, ScheduleFull, TeamRoster, game, index, player, PlayerSchedule, fixtures, season_summary

urlpatterns = [
    url(r'^$', index, name='league_index'),
    url(r'^season/(?P<season_slug>[-\w]+)$', season_summary, name='season' ),
    url(r'^members$', TeamRoster.as_view(), name='club_members' ),
    url(r'^(?P<league>[-\w]+)/standings$', StandingsFull.as_view(), name='standings_full' ),
    url(r'^(?P<league>[-\w]+)/schedule$', ScheduleFull.as_view(), name='schedule_full' ),
    url(r'^(?P<league>[-\w]+)$', fixtures, name='league' ),
    url(r'^game/(?P<game_id>[0-9]+)$', game, name='game'),
    url(r'^player/(?P<player_id>[0-9]+)/(?P<league>[-\w]+)$', player, name='player'),
    url(r'^player/(?P<player_id>[0-9]+)$', player, name='player'),
    #url(r'^(?P<season>[-\w]+)/team/(?P<team>[-\w]+)$', TeamDetails.as_view(), name='team_details' ),
    #url(r'^(?P<season>[-\w]+)/team/(?P<team>[-\w]+)/roster$', TeamRoster.as_view(), name='team_roster' ),
    url(r'^(?P<season>[-\w]+)/members$', TeamRoster.as_view(), name='club_members_by_season' ),

    #url(r'^(?P<season>[-\w]+)/team/(?P<team>[-\w]+)/schedule$', TeamSchedule.as_view(), name='team_schedule' ),
]