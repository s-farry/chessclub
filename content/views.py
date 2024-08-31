# Create your views here.
from django.shortcuts import render
from django.views.generic import TemplateView, View, ListView, DetailView
from .models import news, Puzzle, album, image, simul, page
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, render
from datetime import datetime
from .forms import SimulForm
from django.core.mail import send_mail

from django.urls import resolve


def latest(request, **kwargs):
    if "article" in kwargs.keys():
        article = get_object_or_404(news, id=kwargs["article"])
        return render(request, "news.html", {"news": [article]})
    else:
        return render(
            request, "news.html", {"news": news.objects.order_by("-published_date")}
        )


def details(request):
    return render(request, "details.html")

def rules(request):
    return render(request, "rules.html")

def plain_page(request):
    current_url = resolve(request.path_info).url_name
    contents = page.objects.filter(title=current_url)
    if len(contents) == 0:
        return render(request, "500.html")
    return render(
        request,
        "plain_page.html",
        {
            "content" : contents[0]
        }
    )


def constitution_change(request):
    return render(request, "constitution_change.html")

def puzzles(request):
    puzzles = Puzzle.objects.filter(date__lte=datetime.now().date()).order_by("-date")[
        :7
    ]
    return render(request, "puzzles.html", {"puzzles": puzzles})


def photoalbum(request, **kwargs):
    a = get_object_or_404(album, slug=kwargs["album"])
    images = image.objects.filter(album=a)
    return render(request, "album.html", {"album": a, "images": images})


def simul_interest(request):
    if request.POST:
        form = SimulForm(request.POST)
        if form.is_valid():
            entrant = form.save(commit=True)
            # commit=False tells Django that "Don't send this to database yet.
            # I have more things I want to do with it."

            # student.user = request.user # Set the user object here
            # student.save() # Now you can send it to DB
            email_message = """
            Dear %s,
            Thank you for registering your interest in the simultaneous exhibition to be held on 3rd September at Wallasey Central Conservative Club.
            We'll be in touch at a later day to let you know if your application has been successful. Get in touch with contact@wallaseychessclub.uk in the meantime if you have any questions.
            """ % (
                entrant.name
            )
            send_mail(
                "Wallasey Chess Club Simultaneous Exhibition",
                email_message,
                "contact@wallaseychessclub.uk",
                [entrant.email, "contact@wallaseychessclub.uk"],
                fail_silently=False,
            )

        return render(
            request, "simul_interest.html", {"form": form, "entrant": entrant}
        )
    else:
        form_url = request.META.get("PATH_INFO", None)
        return render(
            request, "simul_interest.html", {"form": SimulForm, "form_url": form_url}
        )


def simul_entrants(request):
    entrants = simul.objects.all().order_by("created_at")
    return render(request, "simul_entrants.html", {"entrants": entrants})


