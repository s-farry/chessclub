# Create your views here.
from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from .models import news
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render

def latest(request):
    return render(request, 'news.html', {'news' : news.objects.order_by("-published_date")[:3]})
def details(request):
    return render(request, 'details.html')