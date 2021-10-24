from django.db import models
from django.utils.translation import ugettext_lazy as _
from smart_selects.db_fields import ChainedManyToManyField, ChainedForeignKey, GroupedForeignKey
from django.utils.timezone import now

from django.db.models import Q
import re

STANDINGS_ORDER_HUMAN = (
    (0, _('Points, Wins, Lost')), 
    (1, _('Points, Tiebreak, Wins, Lost, Rating')), 
    (2, _('Points, Score')), 
    (3, _('FIDE Swiss Tiebreak System'))
)
STANDINGS_ORDER = (
    (0, ('-points', '-win', '-matches', 'lost','-rating', 'player__surename')), 
    (1, ('-points', '-nbs', '-win', 'lost','-rating', 'player__surename')), 
    (2, ('-points',)), 
    (3, ('-points', '-buchholzcut1', '-buchholz', '-oprating', '-win', '-win1', '-matchblack','-nbs','-rating','player__surename'))
)
RESULTS = (
    (0, '1/2-1/2',), (1,'1-0'), (2,'0-1'), (3,'-')
)
TOURNAMENT_FORMATS = (
    (0, 'League',), (1,'Swiss'), (2,'Round Robin'),
)
POINTS = (
    (0, 0), (1,0.5), (2,1), (3, 2), (4,3),
)

from tinymce.widgets import TinyMCE

class MyMCEField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(models.CharField, self).__init__(*args, **kwargs)
        self.widget = TinyMCE(attrs = {'rows' : '30', 'cols' : '100', 'content_style' : "color:#FFFF00"})


class Player(models.Model):
    name = models.CharField(max_length=200, null=True, verbose_name=_('First name'))
    surename = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Last name'))
    birth_date = models.DateField(null=True, blank=True, verbose_name=_('Date of birth'))
    image = models.ImageField(upload_to='uploads/teams/%Y/%m/%d/players/', null=True, blank=True, verbose_name=_('Player photo'))
    lichess = models.CharField(max_length=200, null = True, blank=True, verbose_name=_('Lichess ID'))
    ecf = models.CharField(max_length=7, null = True, blank=True, verbose_name=_('ECF Grading Ref'))
    rating = models.IntegerField(default = 0, null = True, blank=True, verbose_name=_('Rating'))

    class Meta:
        verbose_name = _('Player')
        verbose_name_plural = _('Players')

    def __str__(self):
        if self.surename: return "{} {}".format(self.name, self.surename)
        else: return self.name
    
    
class PlayerCustomFields(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    custom_field_order = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return "{}".format(self.name)

class Season(models.Model):
    name    = models.CharField(max_length=200, null=False, verbose_name=_('Name'))
    players = models.ManyToManyField(Player, blank=True, related_name='seasons', verbose_name=_('Seasons'))
    slug = models.SlugField(unique=True, null=True, verbose_name=_('Slug'))

    def __str__(self):
        return "{}".format(self.name) 

class League(models.Model):
    name = models.CharField(max_length=200, null=False, verbose_name=_('Name'))
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    description = models.CharField(max_length = 10000, blank = True, null = True)
    slug = models.SlugField(unique=True, null=True, verbose_name=_('Slug'))
    players = models.ManyToManyField(Player, blank=True, related_name='players', verbose_name=_('Players'))
    updated_date = models.DateTimeField()
    standings_order = models.IntegerField(verbose_name=_('Standings order'),
        choices=(STANDINGS_ORDER_HUMAN),
        default=0
    )
    win_points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points for win'), choices = (POINTS))
    lost_points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points for loss'), choices = (POINTS))
    draw_points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points for draw'), choices = (POINTS))
    format = models.IntegerField(default = 0, choices=(TOURNAMENT_FORMATS))

    '''
    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {'description': MyMCEField}
        defaults.update(kwargs)
        return super().formfield(**defaults)
    '''
    class Meta:
        verbose_name = _('League')
        verbose_name_plural = _('Leagues')

    def __str__(self):
        return "{0} {1}".format(self.name, self.season)        
        
    def get_rounds(self):
        games = Schedule.objects.filter(league=self)
        return list(set(g.round for g in games if g.round is not None))
    def get_completed_rounds(self):
        games = Schedule.objects.filter((~Q(result=3)) & Q(league = self))
        return list(set(g.round for g in games))

class Schedule(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, verbose_name=_('League'))
    round = models.IntegerField(null=True, blank=True, verbose_name=_('Round'))
    date = models.DateTimeField(verbose_name=_('Date'),blank=True, null=True)
    pgn  = models.TextField(null = True, blank=True)
    white = models.ForeignKey(Player, related_name='white', on_delete=models.CASCADE, verbose_name=_('White'), null = True, blank = True)
    black = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name=_('Black'),
     null = True, blank = True)
    white_rating = models.IntegerField(null = True, blank = True, verbose_name=('White Rating'))
    black_rating = models.IntegerField(null = True, blank = True, verbose_name=('Black Rating'))

    result = models.IntegerField(verbose_name=_('result'),
        choices=(RESULTS),
        default=3
    )
    lichess = models.CharField(max_length=200, null = True, verbose_name=_('Lichess ID'), blank=True)

    class Meta:
        verbose_name = _('Game')
        verbose_name_plural = _('Games')

    def print_result(self, plain = False):
        for a,b in RESULTS:
            if self.result == a:
                if plain: return b
                if b == "1/2-1/2":
                    return r"&#189;-&#189;"
                elif b == "-":
                    return "v"
                else:
                    return b

    def clean_pgn(self):
        pgn = self.pgn
        if pgn:
            pgn = re.sub(r"(\[%clk [0-9]:[0-9]+:[0-9]+\])", '', self.pgn)
            pgn = re.sub(r"(\[%eval [a-zA-Z0-9_\#.-]*\])", '', pgn)
        return pgn

    def __str__(self):
        if self.white and self.black:
            return "{}: {} {} {}".format(self.league, self.white, self.print_result(plain = True), self.black) 
        elif self.white:
            return "{}: {} (bye)".format(self.league, self.white) 
        else:
            return "{}: {} (bye)".format(self.league, self.black) 




class Standings(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, verbose_name=_('League'))
    player = ChainedForeignKey(Player, chained_field='season', chained_model_field='teams', related_name='team', verbose_name=_('Team'))
    position = models.IntegerField(null=True, blank=True, default=1, verbose_name=_('Position'))
    matches = models.IntegerField(null=True, blank=True, default=0, verbose_name=_('Matches'))
    win = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Won'))
    lost = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Lost'))
    draws = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Draw'))
    points = models.FloatField(null=True, blank=False, default=0, verbose_name=_('Points'))
    form = models.CharField(max_length=50,null=True)
    rating = models.IntegerField(null = True, blank = True, verbose_name=('Rating'))
    nbs    = models.FloatField(null=True, blank = False, default = 0, verbose_name=('Neustadtl Sonneborn-Berger Score'))
    buchholzcut1  = models.FloatField(null=True, blank = False, default = 0, verbose_name=('Buchholz Cut 1 Score'))
    buchholz      = models.FloatField(null=True, blank = False, default = 0, verbose_name=('Buchholz Score'))
    opprating = models.FloatField(null = True, blank = True, verbose_name=('Average Rating of Opponent less 1'))
    win1 = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Won With Black'))
    matches1 = models.IntegerField(null=True, blank=True, default=0, verbose_name=_('Matches With Black'))


    def __str__(self):
        return "{0} {1}".format(self.league, self.player)

    def swiss_points(self):
        return ("%.1f"%(self.points)).replace('.',',')
    def swiss_nbs(self):
        return ("%.2f"%(self.nbs)).replace('.',',')


    class Meta:
        ordering = STANDINGS_ORDER[0][1]
        unique_together = ('league', 'player')
        verbose_name = _('Table')
        verbose_name_plural = _('Tables')



# Create your models here.
