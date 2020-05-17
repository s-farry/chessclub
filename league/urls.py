from django.conf.urls import url

from .views import StandingsFull, ScheduleFull, game, index, player

urlpatterns = [
    url(r'^$', index, name='league_index'),
    url(r'^(?P<season>[-\w]+)/standings$', StandingsFull.as_view(), name='standings_full' ),
    url(r'^(?P<season>[-\w]+)/schedule$', ScheduleFull.as_view(), name='schedule_full' ),
    url(r'^game/(?P<game_id>[0-9]+)$', game, name='game'),
    url(r'^player/(?P<player_id>[0-9]+)$', player, name='player')
    #url(r'^(?P<season>[-\w]+)/team/(?P<team>[-\w]+)$', TeamDetails.as_view(), name='team_details' ),
    #url(r'^(?P<season>[-\w]+)/team/(?P<team>[-\w]+)/roster$', TeamRoster.as_view(), name='team_roster' ),
    #url(r'^(?P<season>[-\w]+)/team/(?P<team>[-\w]+)/schedule$', TeamSchedule.as_view(), name='team_schedule' ),
]