from django.contrib import admin
from .models import news, event

# Register your models here.

admin.site.register(news)
admin.site.register(event)