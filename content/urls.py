from django.conf.urls import url

from .views import latest, details, puzzles, photoalbum, simul_interest, simul_entrants

urlpatterns = [
#    url(r'^$', index, name='content_index'),
    url(r'^news$', latest, name='news'),
    url(r'^details$', details, name='details'),
    url(r"^album/(?P<album>[-\w]+)$", photoalbum, name="album"),
    url(r'^content/news$', latest, name='news'),
    url(r'^content/details$', details, name='details'),
    url(r'^puzzles$', puzzles, name='puzzles'),
    url(r'^simul$', simul_interest, name='simul_interest'),
    url(r'^simul_entrants$', simul_entrants, name='simul_entrants')
]