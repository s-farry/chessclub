from django.db import models

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
    title = models.CharField(max_length = 200, default = "Feature")
    text = models.CharField(max_length = 10000)
    synopsis = models.CharField(max_length = 1000, default = '', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='d')
    published_date = models.DateTimeField(auto_now=True, null = True)
    image = models.ImageField(blank=True, upload_to = 'images')

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
        return "%s" % (self.title)
    def __str__(self):              # __unicode__ on Python 2
        return "%s" % (self.title)