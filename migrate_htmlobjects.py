import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "chessclub.settings"
django.setup()

from league.models import Player, Season, League, Schedule, Standings
from content.models import page, snippet

for h in snippet.objects.all():
    if h.type==2:
        
        p = page(
            title=h.title,
            body=h.body,
            active=h.active
        )
        p.save()



for h in snippet.objects.all():
    if h.type==2:
        h.delete()        
