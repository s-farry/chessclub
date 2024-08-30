from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.urls import reverse


from pathlib import Path


STATUS_CHOICES = (
    ("d", "Draft"),
    ("p", "Published"),
    ("w", "Withdrawn"),
)

OBJECT_CHOICES = ((0, "notification"), (1, "about us"), (2, "page"))


class htmlobject(models.Model):
    class Meta:
        verbose_name_plural = "HTML Objects"
        verbose_name = "HTML Object"

    title = models.CharField(max_length=200)
    body = models.TextField(max_length=1000000)
    active = models.BooleanField(default=True)
    type = models.IntegerField(choices=OBJECT_CHOICES, default=0)

    def name(self):
        return "%s" % (self.title)

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        """On save, touch the tmp restart to load up a new page"""
        super(htmlobject, self).save(*args, **kwargs)
        f = Path('/home/themovie/chessclub/tmp/restart.txt')
        if f.exists(): f.touch()    


class menuitem(models.Model):
    class Meta:
        verbose_name_plural = "Menu Items"
        verbose_name = "Menu Item"

    order = models.IntegerField(blank=True, null=True)
    icon = models.CharField(max_length=200, blank=True, null=True)
    text = models.CharField(max_length=200)
    link = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.text

    def url(self):
        if not self.link:
            return self.link
        if self.link.startswith('http') or self.link.startswith('www'):
            return self.link
        split_link = self.link.split()
        if len(split_link) == 0:
            return reverse(split_link)
        elif len(split_link) > 0:
            return reverse(split_link[0], args=split_link[1:])
        else:
            return self.link


class dropdownitem(models.Model):
    class Meta:
        verbose_name_plural = "Dropdown Items"
        verbose_name = "Dropdown Item"

    order = models.IntegerField(blank=True, null=True)
    text = models.CharField(max_length=200)
    link = models.CharField(max_length=200, blank=True, null=True)
    subitem = models.BooleanField(default=False)

    menuitem = models.ForeignKey(
        menuitem,
        on_delete=models.CASCADE,
        verbose_name="Menu Item",
        blank=True,
        null=True,
    )

    def url(self):
        if not self.link:
            return ""
        if self.link.startswith('http') or self.link.startswith('www'):
            return self.link
        split_link = self.link.split()
        if len(split_link) == 0:
            return reverse(split_link)
        elif len(split_link) > 0:
            return reverse(split_link[0], args=split_link[1:])
        else:
            return self.link


class Puzzle(models.Model):
    pgn = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    fen = models.CharField(max_length=50, null=True, blank=True)


# Create your models here.
class news(models.Model):
    class Meta:
        verbose_name_plural = "News"
        permissions = [
            ("publish", "Can mark a news item as published"),
        ]

    title = models.CharField(max_length=200, default="Feature")
    text = models.CharField(max_length=10000)
    caption = models.CharField(max_length=500, blank=True, null=True)
    synopsis = models.CharField(max_length=1000, default="", null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="d")
    published_date = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(blank=True, upload_to="images")
    author = models.ForeignKey(
        User,
        related_name="author",
        on_delete=models.CASCADE,
        verbose_name=("Author"),
        null=True,
        blank=True,
    )
    puzzle = models.ForeignKey(
        Puzzle,
        related_name="puzzle",
        on_delete=models.CASCADE,
        verbose_name=("Puzzle"),
        null=True,
        blank=True,
    )

    def name(self):  # __unicode__ on Python 2
        return "%s" % (self.title)

    def __str__(self):  # __unicode__ on Python 2
        return "%s" % (self.title)


class event(models.Model):
    title = models.CharField(max_length=200, default="Event")
    date = models.DateTimeField()
    link = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    # image = models.ImageField(blank=True, upload_to = 'images')
    # text = models.CharField(max_length = 10000)

    def name(self):  # __unicode__ on Python 2
        return "%s - %s" % (self.title)

    def __str__(self):  # __unicode__ on Python 2
        return "%s - %s, %s" % (self.title, self.date.date(), self.date.time())


class album(models.Model):
    title = models.CharField(max_length=200)
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)

    def name(self):  # __unicode__ on Python 2
        return "%s - %s" % (self.title)

    def __str__(self):  # __unicode__ on Python 2
        return "%s - %s, %s" % (self.title, self.updated.date(), self.updated.time())

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = timezone.now()
            self.slug = slugify("{}".format(self.title))
        self.updated = timezone.now()
        return super(album, self).save(*args, **kwargs)


class image(models.Model):
    description = models.TextField(null=True, blank=True)
    altText = models.TextField(null=True, blank=True)
    album = models.ForeignKey(album, null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, upload_to="images")


class simul(models.Model):
    class Meta:
        verbose_name_plural = "Simul Entrants"

    name = models.CharField(null=False, blank=False, max_length=100)
    email = models.CharField(null=False, blank=False, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # __unicode__ on Python 2
        return self.name


class Document(models.Model):
    specifications = models.FileField(upload_to='docs')
