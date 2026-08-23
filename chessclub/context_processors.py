from django.contrib.auth.models import User
from content.models import snippet, menuitem, dropdownitem

def htmlobjects(request):
    notifications = snippet.objects.all().filter(type=0, active=True)
    menuitems = menuitem.objects.all().order_by('order')
    context = {}
    if len(notifications) > 0:
        context['notifications'] = notifications
    if len(menuitems) > 0:

        main_menuitems = {m : dropdownitem.objects.filter(menuitem=m).order_by('order') for m in menuitem.objects.filter(category=0).order_by('order')}
        season_menuitems = {m : dropdownitem.objects.filter(menuitem=m).order_by('order') for m in menuitem.objects.filter(category=1).order_by('order')}
        club_menuitems = {m : dropdownitem.objects.filter(menuitem=m).order_by('order') for m in menuitem.objects.filter(category=2).order_by('order')}

        #context['menuitems'] = {m : dropdownitem.objects.filter(menuitem=m).order_by('order') for m in menuitems}
        context['menu'] = { 'MAIN' : main_menuitems, 'SEASON' : season_menuitems, 'CLUB' : club_menuitems}
    return context