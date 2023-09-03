from django.contrib.auth.models import User
from content.models import htmlobject, menuitem, dropdownitem

def htmlobjects(request):
    notifications = htmlobject.objects.all().filter(type=0, active=True)
    menuitems = menuitem.objects.all().order_by('order')
    context = {}
    if len(notifications) > 0:
        context['notifications'] = notifications
    if len(menuitems) > 0:
        context['menuitems'] = {m : dropdownitem.objects.filter(menuitem=m).order_by('order') for m in menuitems}
    return context