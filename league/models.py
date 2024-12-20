from django.db import models
from django.utils.translation import ugettext_lazy as _
from smart_selects.db_fields import (
    ChainedManyToManyField,
    ChainedForeignKey,
    GroupedForeignKey,
)
from django.utils.timezone import now

from django.db.models import Q
import re
import math

STANDINGS_ORDER_HUMAN = (
    (0, _("Points, Wins, Lost")),
    (1, _("Points, Tiebreak, Wins, Lost, Rating")),
    (2, _("Points, Score")),
    (3, _("FIDE Swiss Tiebreak System")),
    (4, _("Win Percentage")),
    (5, _("Matches Played")),
    (6, _("Points, Head-to-Head, Wins, Wins With Black, NBS")),
)
STANDINGS_ORDER = (
    (0, ("-points", "-win", "lost", "matches", "-rating", "player__surename")),
    (1, ("-points", "-nbs", "-win", "lost", "-rating", "player__surename")),
    (2, ("-points",)),
    (
        3,
        (
            "-points",
            "-buchholzcut1",
            "-buchholz",
            "-opprating",
            "-win",
            "-win1",
            "-matches1",
            "-nbs",
            "-rating",
            "player__surename",
        )
    ),
    (
        4,
        (
            "-points",
            "-winpercent",
            "-win",
            "lost",
            "matches",
            "-rating",
            "player__surename",
        )
    ),
    (
        5,
        (
            "-points",
            "matches",
            "-win",
            "lost",
            "matches",
            "-rating",
            "player__surename",
        )
    ),
    (
        6,
        (
            "-points",
            "-h2h",
            "-win",
            "-win1",
            "-rating",
            "player__surename",
        )
    ),
)
RESULTS = (
    (
        0,
        "1/2-1/2",
    ),
    (1, "1-0"),
    (2, "0-1"),
    (3, "-"),
    (4, "+--"),
    (5, "--+"),
)
TOURNAMENT_FORMATS = (
    (
        0,
        "League",
    ),
    (1, "Swiss"),
    (2, "Round Robin"),
    (3, "Knockout"),
)
POINTS = (
    (0, 0),
    (1, 0.5),
    (2, 1),
    (3, 2),
    (4, 3),
)
TEAM_SCORES = (
    (-1, 'P'),
    (0, 0),
    (1, 0.5),
    (2, 1),
    (3, 1.5),
    (4, 2),
    (5, 2.5),
    (6, 3),
    (7, 3.5),
    (8, 4),
    (9, 4.5),
    (10, 5),
    (11, 5.5),
    (12, 6),
    (13, 6.5),
    (14, 7),
    (15, 7.5),
    (16, 8),
    (17, 8.5),
    (18, 9),
    (19, 9.5),
    (20, 10),
)
KNOCKOUT_ROUNDS = (
    (0, 'Preliminary'),
    (-1, 'Final'),
    (-2, 'Semi-Final'),
    (-3, 'Quarter Final'),
    (-4, 'Last 16'),
    (-5, 'Last 32'),
    (-6, 'Last 64'),
    (-7, 'Last 128'),
    (1, 'Round 1'),
    (2, 'Round 2'),
    (3, 'Round 3'),
    (4, 'Round 4'),
    (5, 'Round 5'),
    (6, 'Round 6'),
    (7, 'Round 7'),
    (8, 'Round 8'),
    (9, 'Round 9'),
    (10, 'Round 10'),
)


COMMITTEE_POSITIONS = (
    (0, _("President")),
    (1, _("Secretary")),
    (2, _("Assistant Secretary")),
    (3, _("Tournament Secretary")),
    (4, _("Club Steward")),
    (5, _("Auditor")),
    (6, _("Treasurer")),
    (7, _("Club Captain")),
    (8, _("Publicity Officer")),
    (9, _("Promotions Officer")),
    (10, _("Other")),
    (11, _("Publicity Agent")),
    (12, _("Officer Without Portfolio")),
)

from tinymce.widgets import TinyMCE


class MyMCEField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(models.CharField, self).__init__(*args, **kwargs)
        self.widget = TinyMCE(
            attrs={"rows": "30", "cols": "100", "content_style": "color:#FFFF00"}
        )


class Player(models.Model):
    name = models.CharField(max_length=200, null=True, verbose_name=_("First name"))
    surename = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Last name")
    )
    ecf_name = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Name for ECF"))
    address = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Address")
    )
    birth_date = models.DateField(
        null=True, blank=True, verbose_name=_("Date of birth")
    )
    image = models.ImageField(
        upload_to="uploads/teams/%Y/%m/%d/players/",
        null=True,
        blank=True,
        verbose_name=_("Player photo"),
    )
    lichess = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Lichess ID")
    )
    chesscom = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Chess.com ID")
    )
    ecf = models.CharField(
        max_length=7, null=True, blank=True, verbose_name=_("ECF Grading Ref")
    )
    fide = models.CharField(
        max_length=7, null=True, blank=True, verbose_name=_("FIDE ID")
    )
    email = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("email")
    )
    phone = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("phone")
    )
    rating = models.IntegerField(null=True, blank=True, verbose_name=_("ECF Rating"))
    fide_rating = models.IntegerField(null=True, blank=True, verbose_name=_("Fide Rating"))

    joined_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")

    def __str__(self):
        if self.surename:
            return "{} {}".format(self.name, self.surename)
        else:
            return self.name

    def ecf_grade(self):
        grade = 0
        if self.rating and self.rating > 700:
            grade = int(round((self.rating - 700) / 7.5))
        return grade
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.joined_date:
            self.joined_date = now().date()
        return super(Player, self).save(*args, **kwargs)



class PlayerCustomFields(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    custom_field_order = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return "{}".format(self.name)


class Season(models.Model):
    name = models.CharField(max_length=200, null=False, verbose_name=_("Name"))
    players = models.ManyToManyField(
        Player, blank=True, related_name="seasons", verbose_name=_("Players")
    )
    extra_players = models.ManyToManyField(
        Player, blank=True, related_name="seasons_extras", verbose_name=_("Extra Players")
    )
    slug = models.SlugField(unique=True, null=True, verbose_name=_("Slug"))
    results_officer = models.CharField(max_length=200, null=True, blank=True)
    results_officer_address = models.CharField(max_length=200, null=True, blank=True)
    treasurer = models.CharField(max_length=200, null=True, blank=True)
    treasurer_address = models.CharField(max_length=200, null=True, blank=True)

    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    ecf_code = models.CharField(max_length=20, null=True, blank=True)
    event_name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return "{}".format(self.name)


class League(models.Model):
    name = models.CharField(max_length=200, null=False, verbose_name=_("Name"))
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    description = models.CharField(max_length=10000, blank=True, null=True)

    promotion = models.IntegerField(blank=True, null=True)
    playoffs  = models.IntegerField(blank=True, null=True)
    relegation = models.IntegerField(blank=True, null=True)

    slug = models.SlugField(unique=True, null=True, verbose_name=_("Slug"))
    players = models.ManyToManyField(
        Player, blank=True, related_name="players", verbose_name=_("Players")
    )
    updated_date = models.DateTimeField(blank=True, null=True)
    standings_order = models.IntegerField(
        verbose_name=_("Standings order"), choices=(STANDINGS_ORDER_HUMAN), default=0
    )
    win_points = models.IntegerField(
        null=True,
        blank=False,
        default=2,
        verbose_name=_("Points for win"),
        choices=(POINTS),
    )
    lost_points = models.IntegerField(
        null=True,
        blank=False,
        default=0,
        verbose_name=_("Points for loss"),
        choices=(POINTS),
    )
    draw_points = models.IntegerField(
        null=True,
        blank=False,
        default=1,
        verbose_name=_("Points for draw"),
        choices=(POINTS),
    )
    format = models.IntegerField(default=0, choices=(TOURNAMENT_FORMATS))

    class Meta:
        verbose_name = _("League")
        verbose_name_plural = _("Leagues")

    def __str__(self):
        return "{0} {1}".format(self.name, self.season)

    def get_rounds(self):
        games = Schedule.objects.filter(league=self)
        return list(set(g.round for g in games if g.round is not None))

    def get_completed_rounds(self):
        games = Schedule.objects.filter((~Q(result=3)) & Q(league=self))
        return list(set(g.round for g in games))

    def get_round_display(self, round):
        display = 'Round %i' % (round)
        if self.format == 3:
            for r in KNOCKOUT_ROUNDS:
                if round==r[0]:
                    display = r[1]
        return display

    def includes_half_points(self):
        if self.win_points == 1 or self.lost_points == 1 or self.draw_points == 1:
            return True
        
    def get_minus_relegation(self):
        return -self.relegation if self.relegation else None


class Schedule(models.Model):
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        verbose_name=_("League"),
        blank=True,
        null=True,
    )
    round = models.IntegerField(null=True, blank=True, verbose_name=_("Round"))
    board = models.IntegerField(null=True, blank=True, verbose_name=_("Board"))
    date = models.DateTimeField(verbose_name=_("Date"), blank=True, null=True)
    white = models.ForeignKey(
        Player,
        related_name="white",
        on_delete=models.CASCADE,
        verbose_name=_("White"),
        null=True,
        blank=True,
    )
    black = models.ForeignKey(
        Player, on_delete=models.CASCADE, verbose_name=_("Black"), null=True, blank=True
    )
    white_rating = models.IntegerField(
        null=True, blank=True, verbose_name=("White Rating")
    )
    black_rating = models.IntegerField(
        null=True, blank=True, verbose_name=("Black Rating")
    )

    result = models.IntegerField(verbose_name=_("result"), choices=(RESULTS), default=3)
    lichess = models.CharField(
        max_length=200, null=True, verbose_name=_("Lichess ID"), blank=True
    )
    comment = models.CharField(
        max_length=200, null=True, verbose_name=_("Comment"), blank=True
    )

    class Meta:
        verbose_name = _("Game")
        verbose_name_plural = _("Games")

    def print_result(self, plain=False):
        for a, b in RESULTS:
            if self.result == a:
                if plain:
                    return b
                if b == "1/2-1/2":
                    return r"&#189;-&#189;"
                elif b == "-":
                    return "v"
                elif b == "--+":
                    return "&#65293;&#65291;"
                elif b == "+--":
                    return "&#65291;&#65293;"
                else:
                    return b

    def get_result(self, plain=False):
        for a, b in RESULTS:
            if self.result == a:
                if b == "1/2-1/2":
                    if plain:
                        return ("1/2", "1/2")
                    else:
                        return ("&#189;", "&#189;")
                elif b == "1-0":
                    return ("1", "0")
                elif b == "0-1":
                    return ("0", "1")
                elif b == "-":
                    return (
                        "-",
                        "-",
                        "v",
                    )
                elif b == "--+":
                    return ("&#65293;", "&#65291;")
                elif b == "+--":
                    return ("&#65291;", "&#65293;")
                else:
                    return (b,)

    def get_white_points(self):
        for a, b in RESULTS:
            if self.result == a:
                if b == "1/2-1/2":
                    return self.league.get_draw_points_display()
                elif b == "1-0":
                    return self.league.get_win_points_display()
                elif b == "0-1":
                    return self.league.get_lost_points_display()
                else:
                    return 0

    def get_black_points(self):
        for a, b in RESULTS:
            if self.result == a:
                if b == "1/2-1/2":
                    return self.league.get_draw_points_display()
                elif b == "1-0":
                    return self.league.get_lost_points_display()
                elif b == "0-1":
                    return self.league.get_win_points_display()
                else:
                    return 0

    def get_ecf_result(self, plain=False):
        for a, b in RESULTS:
            if self.result == a:
                if b == "1/2-1/2":
                    return "55"
                elif b == "1-0":
                    return "10"
                elif b == "0-1":
                    return "01"
                else:
                    return b

    def get_round_display(self):
        return self.league.get_round_display(self.round)

    def __str__(self):
        date = ""
        if self.date:
            date = self.date.date()
        if self.white and self.black:
            return "{}: {} {} {}".format(
                date, self.white, self.print_result(plain=True), self.black
            )
        elif self.white:
            return "{}: {}".format(date, self.white)
        else:
            return "{}: {}".format(date, self.black)


class PGN(models.Model):
    body = models.TextField()
    game = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, verbose_name=_("Game"), related_name="pgn"
    )

    def __str__(self):
        return self.game.__str__()


class Team(models.Model):
    name = models.CharField(max_length=200, null=True, verbose_name=_("Team Name"))
    captain = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        verbose_name=_("Team Captain"),
        related_name="captain",
        null=True,
        blank=True,
    )
    league = models.CharField(max_length=200, null=True, verbose_name=_("League"))
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    description = models.CharField(max_length=10000, blank=True, null=True)

    def __str__(self):
        return "%s (%s)" % (self.name, self.season)


class TeamFixture(models.Model):
    date = models.DateTimeField(verbose_name=_("Date"), blank=True, null=True)
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, verbose_name=_("Team"), null=True, blank=True
    )
    opponent = models.CharField(max_length=200, null=True, verbose_name=_("Opponent"))
    home_score = models.IntegerField(null=True, blank=True, choices=TEAM_SCORES)
    away_score = models.IntegerField(null=True, blank=True, choices=TEAM_SCORES)
    home = models.BooleanField()

    class Meta:
        verbose_name = _("Team Fixture")
        verbose_name_plural = _("Team Fixtures")

    def __str__(self):
        if self.home:
            return "%s v %s" % (self.team.name, self.opponent)
        else:
            return "%s v %s" % (self.opponent, self.team.name)

    def print_result(self, plain=False):
        if self.home_score is None or self.away_score is None:
            return "v"
        elif self.home_score == -1 or self.away_score == -1:
            return 'P - P'
        else:
            home_score = self.home_score / 2.0
            away_score = self.away_score / 2.0
            if home_score == 0.5:
                home_display_score = "&#189;"
            elif home_score % 1 == 0.5:
                home_display_score = "%i&#189;" % (math.floor(home_score))
            else:
                home_display_score = "%i" % (math.floor(home_score))
            if away_score == 0.5:
                away_display_score = "&#189;"
            elif away_score % 1 == 0.5:
                away_display_score = "%i&#189;" % (math.floor(away_score))
            else:
                away_display_score = "%i" % (math.floor(away_score))

            return "%s - %s" % (home_display_score, away_display_score)


class TeamPlayer(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name=_("Team"))
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, verbose_name=_("Team Player")
    )
    listed = models.BooleanField(default=False)
    played = models.IntegerField(default=0, null=True, blank=True)
    won = models.IntegerField(default=0, null=True, blank=True)
    draw = models.IntegerField(default=0, null=True, blank=True)
    lost = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        verbose_name = _("Team Player")
        verbose_name_plural = _("Team Players")

    def __str__(self):
        return "%s - %s" % (self.player, self.team.name)


class CommitteeMember(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, verbose_name=_("Season"))
    member = models.ForeignKey(
        Player, on_delete=models.CASCADE, verbose_name=_("Committee Member")
    )
    position = models.IntegerField(
        verbose_name=_("Committe Position"), choices=(COMMITTEE_POSITIONS), null=True, blank=True
    )
    start_date = models.DateField(
        null=True, blank=True, verbose_name=_("Start Date")
    )
    end_date = models.DateField(
        null=True, blank=True, verbose_name=_("End Date")
    )
    class Meta:
        verbose_name = _("Committee Member")
        verbose_name_plural = _("Committee Members")

    def __str__(self):
        return "%s - %s" % (self.position, self.member)


class Standings(models.Model):
    league = models.ForeignKey(
        League, on_delete=models.CASCADE, verbose_name=_("League")
    )
    player = ChainedForeignKey(
        Player,
        chained_field="season",
        chained_model_field="teams",
        related_name="team",
        verbose_name=_("Team"),
    )
    position = models.IntegerField(
        null=True, blank=True, verbose_name=_("Position")
    )
    matches = models.IntegerField(
        null=True, blank=True, default=0, verbose_name=_("Matches")
    )
    win = models.IntegerField(null=True, blank=False, default=0, verbose_name=_("Won"))
    lost = models.IntegerField(
        null=True, blank=False, default=0, verbose_name=_("Lost")
    )
    draws = models.IntegerField(
        null=True, blank=False, default=0, verbose_name=_("Draw")
    )
    points = models.FloatField(
        null=True, blank=False, default=0, verbose_name=_("Points")
    )
    form = models.CharField(max_length=50, null=True)
    rating = models.IntegerField(null=True, blank=True, verbose_name=("Rating"))

    # these are all potential tie breaker metrics
    nbs = models.FloatField(
        null=True,
        blank=False,
        default=0,
        verbose_name=("Neustadtl Sonneborn-Berger Score"),
    )
    buchholzcut1 = models.FloatField(
        null=True, blank=False, default=0, verbose_name=("Buchholz Cut 1 Score")
    )
    buchholz = models.FloatField(
        null=True, blank=False, default=0, verbose_name=("Buchholz Score")
    )
    opprating = models.FloatField(
        null=True, blank=True, verbose_name=("Average Rating of Opponent less 1")
    )
    win1 = models.IntegerField(
        null=True, blank=False, default=0, verbose_name=_("Won With Black")
    )
    matches1 = models.IntegerField(
        null=True, blank=True, default=0, verbose_name=_("Matches With Black")
    )
    performance = models.FloatField(
        null=True, blank=True, default=0, verbose_name=_("Performance Rating")
    )
    winpercent = models.FloatField(
        null=True, blank=True, default=0, verbose_name=_("Win Percentage")
    )
    h2h = models.IntegerField(
        null=True, blank=True, default=0, verbose_name=_("Head to Head Record")
    )

    def __str__(self):
        return "{0} {1}".format(self.league, self.player)

    def swiss_points(self):
        return ("%.1f" % (self.points)).replace(".", ",")

    def swiss_nbs(self):
        return ("%.2f" % (self.nbs)).replace(".", ",")

    def total_points(self):
        league = self.league
        w, d, l = league.win_points, league.draw_points, league.lost_points
        if w % 1 == 0 and d % 1 == 0 and l % 1 == 0:
            return "%i" % (int(self.points))
        elif w % 1 == 0.5 or d % 1 == 0.5 or l % 1 == 0.5:
            return self.swiss_points()
        else:
            return "%.2f" % (self.points)

    class Meta:
        ordering = STANDINGS_ORDER[0][1]
        unique_together = ("league", "player")
        verbose_name = _("Table")
        verbose_name_plural = _("Tables")


# Create your models here.
