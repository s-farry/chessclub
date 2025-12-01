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

# processors.py
from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill, Adjust
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, SmartResize

from PIL import Image, ImageOps

import cv2
import numpy as np
from PIL import Image

class SmartCrop:
    """
    Intelligently crop images focusing on faces or the most interesting area
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Don't store the cascade classifier - load it in process() instead
    
    def detect_faces(self, image):
        """Detect faces in the image"""
        # Load cascade classifier here (not in __init__)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces
    
    def process(self, image):
        # Calculate target aspect ratio
        target_ratio = self.width / self.height
        img_ratio = image.width / image.height
        
        # Detect faces
        faces = self.detect_faces(image)
        
        if img_ratio > target_ratio:
            # Image is wider - crop sides
            new_width = int(image.height * target_ratio)
            
            if len(faces) > 0:
                # Calculate center of all faces
                face_center_x = int(np.mean([x + w/2 for x, y, w, h in faces]))
                # Center crop around faces
                left = max(0, min(face_center_x - new_width // 2, 
                                 image.width - new_width))
            else:
                # No faces - center crop
                left = (image.width - new_width) // 2
            
            image = image.crop((left, 0, left + new_width, image.height))
            
        elif img_ratio < target_ratio:
            # Image is taller - crop top/bottom
            new_height = int(image.width / target_ratio)
            
            if len(faces) > 0:
                # Calculate center of all faces
                face_center_y = int(np.mean([y + h/2 for x, y, w, h in faces]))
                # Center crop around faces, but don't crop too high
                top = max(0, min(face_center_y - new_height // 2, 
                                image.height - new_height))
            else:
                # No faces - bias toward top (70/30 split)
                top = int((image.height - new_height) * 0.3)
            
            image = image.crop((0, top, image.width, top + new_height))
        
        # Resize to exact dimensions
        return image.resize((self.width, self.height), Image.Resampling.LANCZOS)
    

class snippet(models.Model):
    class Meta:
        verbose_name_plural = "Snippets"
        verbose_name = "Snippet"

    title = models.CharField(max_length=200)
    body = models.TextField(max_length=1000000)
    active = models.BooleanField(default=True)
    type = models.IntegerField(choices=OBJECT_CHOICES, default=0)

    def name(self):
        return "%s" % (self.title)

    def __str__(self):
        return "%s" % (self.title)



class page(models.Model):
    class Meta:
        verbose_name_plural = "Plain Pages"
        verbose_name = "Plain Page"

    title = models.CharField(max_length=200)
    body = models.TextField(max_length=1000000)
    active = models.BooleanField(default=True)
    
    def name(self):
        return "%s" % (self.title)

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        """On save, touch the tmp restart to load up a new page"""
        super(page, self).save(*args, **kwargs)
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
        if self.link.startswith('http') or self.link.startswith('www') or self.link.startswith('/'):
        
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
            ("publish_news", "Can mark a news item as published"),
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


    # Home page thumbnail - fixed aspect ratio for consistency
    image_thumbnail = ImageSpecField(
        source='image',
        processors=[SmartCrop(400, 300)],  # 4:3 aspect ratio
        format='JPEG',
        options={'quality': 85}
    )
    
    # Article page header - flexible height, intelligent crop
    image_header = ImageSpecField(
        source='image',
        processors=[SmartCrop(1200, 400)],  # Max 1200w x 600h, maintains aspect
        format='JPEG',
        options={'quality': 90}
    )
    
    # Optional: Different sizes for different uses
    image_card = ImageSpecField(
        source='image',
        processors=[SmartCrop(350, 250)],
        format='JPEG',
        options={'quality': 85}
    )


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
