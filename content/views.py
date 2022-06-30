# Create your views here.
from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from .models import news, Puzzle, album, image
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render
from datetime import datetime

def latest(request):
    return render(request, 'news.html', {'news' : news.objects.order_by("-published_date")})
def details(request):
    return render(request, 'details.html')
def puzzles(request):
    puzzles = Puzzle.objects.filter(date__lte=datetime.now().date() ).order_by("-date")[:7]
    return render(request, 'puzzles.html', {'puzzles' : puzzles })

def photoalbum(request, **kwargs):
    a = get_object_or_404(album, slug=kwargs["album"])
    images = image.objects.filter(album=a)
    return render(request, 'album.html', {'album' : a, 'images' : images})