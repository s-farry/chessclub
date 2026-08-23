import io
import logging

from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, View, ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Q

from league.models import Schedule, Standings, League, Player, STANDINGS_ORDER, TeamFixture, LMSTeamFixture, Season
from content.models import news, event, Puzzle, page, snippet

log = logging.getLogger(__name__)

# ---- Summernote image-compression upload override ----

_IMG_THRESHOLD = 1 * 1024 * 1024   # compress images larger than 1 MB
_IMG_MAX_DIM   = 2048               # max width or height after resize
_IMG_QUALITY   = 82                 # initial JPEG quality


def _compress_image(f):
    """Return (file, was_compressed). Falls back to the original on any error."""
    try:
        from PIL import Image
        f.seek(0)
        img = Image.open(f)
        img.load()
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        w, h = img.size
        if w > _IMG_MAX_DIM or h > _IMG_MAX_DIM:
            if w >= h:
                h = round(h * _IMG_MAX_DIM / w); w = _IMG_MAX_DIM
            else:
                w = round(w * _IMG_MAX_DIM / h); h = _IMG_MAX_DIM
            img = img.resize((w, h), Image.LANCZOS)
        quality = _IMG_QUALITY
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=quality, optimize=True)
        while buf.tell() > _IMG_THRESHOLD and quality > 40:
            quality -= 10
            buf = io.BytesIO()
            img.save(buf, 'JPEG', quality=quality, optimize=True)
        buf.seek(0)
        stem = f.name.rsplit('.', 1)[0] if '.' in f.name else f.name
        return ContentFile(buf.read(), name=stem + '.jpg'), True
    except Exception:
        try:
            f.seek(0)
        except Exception:
            pass
        return f, False


class CompressedSummernoteUpload(View):
    """
    Replaces django-summernote's SummernoteUploadAttachment.
    Images over 1 MB are compressed via Pillow before saving;
    otherwise behaviour is identical to the original view.
    """

    @method_decorator(xframe_options_sameorigin)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        from django_summernote.utils import get_config, get_attachment_model

        config = get_config()

        if config['disable_attachment']:
            return JsonResponse(
                {'status': 'false', 'message': _('Attachment module is disabled')}, status=403)
        if config['attachment_require_authentication'] and not request.user.is_authenticated:
            return JsonResponse(
                {'status': 'false', 'message': _('Only authenticated users are allowed')}, status=403)

        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse(
                {'status': 'false', 'message': _('No files were requested')}, status=400)

        post_kwargs = request.POST.copy()
        post_kwargs.pop('csrfmiddlewaretoken', None)

        try:
            attachments = []
            for f in files:
                is_image = f.content_type and f.content_type.startswith('image/')
                if is_image and f.size > _IMG_THRESHOLD:
                    f, compressed = _compress_image(f)
                    if compressed:
                        log.info('Compressed uploaded image to %d bytes', len(f))
                elif not is_image and f.size > config['attachment_filesize_limit']:
                    return JsonResponse(
                        {'status': 'false',
                         'message': _('File size exceeds the limit allowed and cannot be saved')},
                        status=400)

                klass = get_attachment_model()
                att = klass()
                att.file = f
                att.save(**post_kwargs)
                att.url = att.file.url
                if config['attachment_absolute_uri']:
                    att.url = request.build_absolute_uri(att.url)
                attachments.append(att)

            return HttpResponse(
                render_to_string('django_summernote/upload_attachment.json',
                                 {'attachments': attachments}),
                content_type='application/json',
            )
        except IOError:
            return JsonResponse(
                {'status': 'false', 'message': _('Failed to save attachment')}, status=500)


def index(request):
    news_objects = news.objects.order_by("-published_date")[:3]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())

    about = snippet.objects.filter(title='About Us')[0]

    current_season = Season.objects.order_by('end').last()
    member_count = current_season.players.count() if current_season else 0
    league_count = League.objects.filter(season=current_season).count() if current_season else 0

    _next_lms = LMSTeamFixture.objects.filter(
        Q(date__gte=timezone.now()),
        Q(home_team__icontains='wallasey') | Q(away_team__icontains='wallasey')
    ).order_by('date').first()
    next_lms_fixtures = list(LMSTeamFixture.objects.filter(
        Q(home_team__icontains='wallasey') | Q(away_team__icontains='wallasey'),
        date__date=_next_lms.date.date()
    ).order_by('date')) if _next_lms else []

    _next_fix = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by('date').first()
    next_fixtures = list(TeamFixture.objects.filter(
        date__date=_next_fix.date.date()
    ).order_by('date')) if _next_fix else []

    # Featured league standings (top 6)
    featured_league = current_season.featured_league if current_season else None
    featured_standings = []
    if featured_league:
        order = STANDINGS_ORDER[featured_league.standings_order][1]
        featured_standings = list(
            Standings.objects.filter(league=featured_league).order_by(*order)[:6]
        )

    return render(
        request,
        "index.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures": team_fixtures,
            "about": about,
            "next_lms_fixtures": next_lms_fixtures,
            "next_fixtures": next_fixtures,
            "member_count": member_count,
            "league_count": league_count,
            "featured_league": featured_league,
            "featured_standings": featured_standings,
        },
    )


def index_test(request):
    news_objects = news.objects.order_by("-published_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())

    about = snippet.objects.filter(title='About Us')[0]

    return render(
        request,
        "index2.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures" : team_fixtures,
            "about" : about
        },
    )

def index_test2(request):
    news_objects = news.objects.order_by("-published_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())

    about = snippet.objects.filter(title='About Us')[0]

    return render(
        request,
        "index3.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures" : team_fixtures,
            "about" : about
        },
    )

def preview(request):
    news_objects = news.objects.order_by("-created_date")[:9]
    events_objects = event.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]
    team_fixtures = TeamFixture.objects.filter(Q(date__gte=timezone.now())).order_by("date")[
        :5
    ]

    team_fixtures = [ f for f in team_fixtures if not (f.home and 'wallasey' in f.opponent.lower())]
    puzzles = Puzzle.objects.filter(date=timezone.localdate())
    return render(
        request,
        "index.html",
        {
            "leagues": League.objects.all(),
            "news": news_objects,
            "events": events_objects,
            "puzzles": puzzles,
            "fixtures" : team_fixtures,
        },
    )

def design_test(request):
    return render(request, "design_test.html")

def page_not_found(request, *args, **kwargs):
    return render(request, "404.html", *args, **kwargs)


def server_error(request, *args, **kwargs):
    return render(request, "500.html", *args, **kwargs)
