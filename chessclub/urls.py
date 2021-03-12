"""chessclub URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url,include
from django.conf import settings
from django.conf.urls.static import static


import league.urls
from . import views
from .admin import *
admin.site = admin_site
admin.autodiscover()
urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    url(r'^$', views.index, name='index'),
    #path('league/', league.urls),
    url(r'^league/', include('league.urls')),
    url(r'^content/', include('content.urls')),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
]

handler404 = 'chessclub.views.page_not_found'
handler500 = 'chessclub.views.page_not_found'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

