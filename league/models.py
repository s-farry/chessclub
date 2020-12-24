from django.db import models
from django.utils.translation import ugettext_lazy as _
from smart_selects.db_fields import ChainedManyToManyField, ChainedForeignKey, GroupedForeignKey
from django.utils.timezone import now


STANDINGS_ORDER_HUMAN = (
    (0, _('Points, Wins, Lost')), 
    (1, _('Points, Score')), 
)
STANDINGS_ORDER = (
    (0, ('-points', '-win', 'lost')), 
    (1, ('-points',)), 
)
RESULTS = (
    (0, '1/2-1/2',), (1,'1-0'), (2,'0-1'), (3,'-')
)


class Player(models.Model):
    name = models.CharField(max_length=200, null=True, verbose_name=_('First name'))
    surename = models.CharField(max_length=200, null=True, verbose_name=_('Last name'))
    birth_date = models.DateField(null=True, blank=True, verbose_name=_('Date of birth'))
    image = models.ImageField(upload_to='uploads/teams/%Y/%m/%d/players/', null=True, blank=True, verbose_name=_('Player photo'))
    lichess = models.CharField(max_length=200, null = True, blank=True, verbose_name=_('Lichess ID'))
    ecf = models.CharField(max_length=7, null = True, blank=True, verbose_name=_('ECF Grading Ref'))
    grade = models.IntegerField(default = 0, null = True, blank=True, verbose_name=_('ECF Grade'))

    class Meta:
        verbose_name = _('Player')
        verbose_name_plural = _('Players')

    def __str__(self):
        return "{} {}".format(self.name, self.surename)
    
    
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
        return "{} Season".format(self.name) 

class League(models.Model):
    name = models.CharField(max_length=200, null=False, verbose_name=_('Name'))
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, null=True, verbose_name=_('Slug'))
    players = models.ManyToManyField(Player, blank=True, related_name='players', verbose_name=_('Players'))
    updated_date = models.DateTimeField()
    standings_order = models.IntegerField(verbose_name=_('Standings order'),
        choices=(STANDINGS_ORDER_HUMAN),
        default=0
    )
    win_points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points for win'))
    lost_points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points for loss'))
    draw_points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points for draw'))

    class Meta:
        verbose_name = _('League')
        verbose_name_plural = _('Leagues')

    def __str__(self):
        return "{0} {1}".format(self.name, self.season)        
        


class Schedule(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, verbose_name=_('League'))
    round = models.IntegerField(null=True, blank=True, default=0, verbose_name=_('Round'))
    date = models.DateTimeField(default=now, verbose_name=_('Date'))
    pgn  = models.TextField(null = True, blank=True)
    white = models.ForeignKey(Player, related_name='white', on_delete=models.CASCADE, verbose_name=_('White'))
    black = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name=_('Black'))
    result = models.IntegerField(verbose_name=_('result'),
        choices=(RESULTS),
        default=3
    )
    lichess = models.CharField(max_length=200, null = True, verbose_name=_('Lichess ID'))

    class Meta:
        verbose_name = _('Game')
        verbose_name_plural = _('Games')

    def print_result(self):
        for a,b in RESULTS:
            if self.result == a: return b
    

    def __str__(self):
        return "{}: {} v {}".format(self.league, self.white, self.black) 



class Standings(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, verbose_name=_('League'))
    player = ChainedForeignKey(Player, chained_field='season', chained_model_field='teams', related_name='team', verbose_name=_('Team'))
    position = models.IntegerField(null=True, blank=True, default=1, verbose_name=_('Position'))
    matches = models.IntegerField(null=True, blank=True, default=0, verbose_name=_('Matches'))
    win = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Won'))
    lost = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Lost'))
    draws = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Draw'))
    points = models.IntegerField(null=True, blank=False, default=0, verbose_name=_('Points'))
    form = models.CharField(max_length=5,null=True)

    def __str__(self):
        return "{0} {1}".format(self.league, self.player)

    class Meta:
        ordering = STANDINGS_ORDER[0][1]
        unique_together = ('league', 'player')
        verbose_name = _('Table')
        verbose_name_plural = _('Tables')



# Create your models here.
