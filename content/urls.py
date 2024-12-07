from django.urls import re_path

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
    re_path(r"^news$", latest, name="news"),
    re_path(r"^news/(?P<article>[-\w]+)$", latest, name="news"),
    re_path(r"^album/(?P<album>[-\w]+)$", photoalbum, name="album"),
    re_path(r"^puzzles$", puzzles, name="puzzles"),
    re_path(r"^simul$", simul_interest, name="simul_interest"),
    re_path(r"^simul_entrants$", simul_entrants, name="simul_entrants"),
    re_path(r"^constitution_change$", constitution_change, name="constitution_change"),
]

urlpatterns += [
    re_path(r"^{}".format(h.title), plain_page, name=h.title)
    for h in page.objects.all().filter(active=True)
]



