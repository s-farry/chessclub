from django.conf.urls import url

from .views import latest, details

urlpatterns = [
#    url(r'^$', index, name='content_index'),
    url(r'^news$', latest, name='news'),
    url(r'^details$', details, name='details'),
]