from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.defaultfilters import slugify

STATUS_CHOICES = (
    ('d', 'Draft'),
    ('p', 'Published'),
    ('w', 'Withdrawn'),
)

class Puzzle(models.Model):
    pgn  = models.TextField(null = True, blank=True)
    date = models.DateField(null = True, blank = True)
    fen = models.CharField(max_length=50, null = True, blank = True)
    
# Create your models here.
class news(models.Model):
    class Meta:
        verbose_name_plural = "News"
        permissions = [
            ("publish", "Can mark a news item as published"),
        ]

    title = models.CharField(max_length = 200, default = "Feature")
    text = models.CharField(max_length = 10000)
    synopsis = models.CharField(max_length = 1000, default = '', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='d')
    published_date = models.DateTimeField(null = True, blank = True)
    image = models.ImageField(blank=True, upload_to = 'images')
    author = models.ForeignKey(User, related_name='author', on_delete=models.CASCADE, verbose_name=('Author'), null = True, blank = True)

    def name(self):              # __unicode__ on Python 2
        return "%s" % (self.title)
    def __str__(self):              # __unicode__ on Python 2
        return "%s" % (self.title)

class event(models.Model):
    title = models.CharField(max_length = 200, default = "Event")
    date = models.DateTimeField()
    link = models.CharField(max_length=200, blank = True, null = True)
    location = models.CharField(max_length=200, blank = True, null = True)

    def name(self):              # __unicode__ on Python 2
        return "%s - %s" % (self.title)
    def __str__(self):              # __unicode__ on Python 2
        return "%s - %s, %s" % (self.title,self.date.date(), self.date.time())



class album(models.Model):
    title = models.CharField(max_length = 200)
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    def name(self):              # __unicode__ on Python 2
        return "%s - %s" % (self.title)
    def __str__(self):              # __unicode__ on Python 2
        return "%s - %s, %s" % (self.title,self.updated.date(), self.updated.time())

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
            self.slug = slugify('{}'.format(self.title))
        self.updated = timezone.now()
        return super(album, self).save(*args, **kwargs)


class image(models.Model):
    description = models.TextField(null=True, blank=True)
    altText = models.TextField(null=True, blank=True)
    album = models.ForeignKey(album, null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, upload_to = 'images')

class simul(models.Model):
    class Meta:
        verbose_name_plural = "Simul Entrants"
    name = models.CharField(null = False, blank = False, max_length=100)
    email = models.CharField(null = False, blank = False, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):              # __unicode__ on Python 2
        return self.name
