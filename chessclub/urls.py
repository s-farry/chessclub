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
from django.urls import path, re_path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
import os

from django.contrib.auth import get_user_model


import league.urls
from . import views
from .admin import *

admin.site = admin_site
admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    re_path(r"^$", views.index, name="index"),
    # path('league/', league.urls),
    re_path(r"^", include("league.urls")),
    re_path(r"^", include("content.urls")),
    re_path(r"^chaining/", include("smart_selects.urls")),
    re_path(r"^tinymce/", include("tinymce.urls")),
]
if "DJANGO_DEBUG" in os.environ and os.environ["DJANGO_DEBUG"] == "1":
    urlpatterns += [
        re_path(r"^404/$", views.page_not_found),
        re_path(r"^500/$", views.server_error),
    ]


handler404 = "chessclub.views.page_not_found"
handler500 = "chessclub.views.server_error"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
