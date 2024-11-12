from django.conf.urls import url

from .models import page

from .views import (
    latest,
    details,
    puzzles,
    photoalbum,
    simul_interest,
    simul_entrants,
    rules,
    constitution_change,
    plain_page
)

urlpatterns = [
    url(r"^news$", latest, name="news"),
    url(r"^news/(?P<article>[-\w]+)$", latest, name="news"),
    url(r"^album/(?P<album>[-\w]+)$", photoalbum, name="album"),
    url(r"^puzzles$", puzzles, name="puzzles"),
    url(r"^simul$", simul_interest, name="simul_interest"),
    url(r"^simul_entrants$", simul_entrants, name="simul_entrants"),
    url(r"^constitution_change$", constitution_change, name="constitution_change"),
]

urlpatterns += [
    url(r"^{}".format(h.title), plain_page, name=h.title)
    for h in page.objects.all().filter(active=True)
]



