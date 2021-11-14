from django.conf.urls import url

from .views import latest, details, puzzles

urlpatterns = [
#    url(r'^$', index, name='content_index'),
    url(r'^news$', latest, name='news'),
    url(r'^details$', details, name='details'),
    url(r'^content/news$', latest, name='news'),
    url(r'^content/details$', details, name='details'),
    url(r'^puzzles$', puzzles, name='puzzles'),
]