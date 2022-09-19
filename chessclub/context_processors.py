from django.contrib.auth.models import User
from content.models import htmlobject

def htmlobjects(request):
    notifications = htmlobject.objects.all().filter(title='Notification')
    context = {}
    if len(notifications) > 0:
        context['notification'] = notifications[0]
    return context