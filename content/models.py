from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.urls import reverse, NoReverseMatch


from pathlib import Path


STATUS_CHOICES = (
    ("d", "Draft"),
    ("p", "Published"),
    ("w", "Withdrawn"),
)

OBJECT_CHOICES = ((0, "notification"), (1, "about us"), (2, "page"))

CATEGORY_CHOICES = ((0, 'MAIN'), (1, 'SEASON'), (2, 'CLUB'))

# processors.py
from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill, Adjust
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, SmartResize

from PIL import Image, ImageOps

import cv2
import numpy as np
import os
from PIL import Image

_YUNET_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'face_detection_yunet_2023mar.onnx')

class SmartCrop:
    """
    Intelligently crop images focusing on faces or the most interesting area
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def detect_faces(self, image):
        if not os.path.exists(_YUNET_MODEL_PATH):
            return []
        orig_w, orig_h = image.width, image.height

        # YuNet works best up to ~1600px; downscale larger images
        max_dim = 1600
        if max(orig_w, orig_h) > max_dim:
            scale = max_dim / max(orig_w, orig_h)
            detect_img = image.resize(
                (int(orig_w * scale), int(orig_h * scale)), Image.Resampling.LANCZOS
            )
        else:
            scale = 1.0
            detect_img = image

        bgr = cv2.cvtColor(np.array(detect_img.convert('RGB')), cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]

        detector = cv2.FaceDetectorYN.create(
            _YUNET_MODEL_PATH, '', (w, h),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=100,
        )
        _, detections = detector.detect(bgr)

        if detections is None:
            return []

        faces = []
        for d in detections:
            x, y, fw, fh = int(d[0]), int(d[1]), int(d[2]), int(d[3])
            # Scale back to original image coords
            x  = max(0, int(x  / scale))
            y  = max(0, int(y  / scale))
            fw = min(int(fw / scale), orig_w - x)
            fh = min(int(fh / scale), orig_h - y)
            faces.append((x, y, fw, fh))

        return faces

    def _face_bounding_box(self, faces, padding_ratio=0.25):
        """Return (min_x, min_y, max_x, max_y, weighted_cx, weighted_cy).
        Extents cover all faces; the weighted centroid is pulled toward larger faces."""
        min_x = min(f[0] for f in faces)
        max_x = max(f[0] + f[2] for f in faces)

        # Quadratic area-weighted centroid — closer (larger) faces count much more
        areas = [(f[2] * f[3]) ** 2 for f in faces]
        total = sum(areas)
        cx = int(sum((f[0] + f[2] / 2) * a for f, a in zip(faces, areas)) / total)
        cy = int(sum((f[1] + f[3] / 2) * a for f, a in zip(faces, areas)) / total)

        pad_x = int((max_x - min_x) * padding_ratio)

        return (min_x - pad_x, max_x + pad_x, cx, cy)

    def process(self, image):
        target_ratio = self.width / self.height
        img_ratio = image.width / image.height

        faces = self.detect_faces(image)

        crop_left, crop_top = 0, 0

        if img_ratio > target_ratio:
            # Image is wider - crop sides
            new_width = int(image.height * target_ratio)

            if len(faces) > 0:
                fx1, fx2, wcx, wcy = self._face_bounding_box(faces)
                faces_width = fx2 - fx1
                if faces_width < new_width:
                    crop_left = max(0, min(wcx - new_width // 2,
                                          image.width - new_width))
                else:
                    crop_left = max(0, min(fx1, image.width - new_width))
            else:
                crop_left = (image.width - new_width) // 2

            image = image.crop((crop_left, 0, crop_left + new_width, image.height))

        elif img_ratio < target_ratio:
            # Image is taller - crop top/bottom
            new_height = int(image.width / target_ratio)

            if len(faces) > 0:
                fx1, fx2, wcx, wcy = self._face_bounding_box(faces)
                # Bias upward slightly so foreheads aren't cropped
                wcy = max(0, wcy - int(new_height * 0.05))
                crop_top = max(0, min(wcy - new_height // 2,
                                      image.height - new_height))
            else:
                crop_top = int((image.height - new_height) * 0.3)

            image = image.crop((0, crop_top, image.width, crop_top + new_height))

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
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    
    def name(self):
        return "%s" % (self.title)

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        """On save, touch the tmp restart to load up a new page"""
        if not self.id or not self.slug:
            self.slug = slugify("{}".format(self.title))
        super(page, self).save(*args, **kwargs)
        f = Path('/home/themovie/chessclub/tmp/restart.txt')
        if f.exists(): f.touch()

class menuitem(models.Model):
    class Meta:
        verbose_name_plural = "Menu Items"
        verbose_name = "Menu Item"
        ordering = ['order']

    order = models.IntegerField(blank=True, null=True)

    category = models.IntegerField(choices=CATEGORY_CHOICES, default=0, help_text="Sidebar section label, e.g. 'Main', 'League', 'Club'")
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
        if not split_link:
            return ''
        try:
            return reverse(split_link[0], args=split_link[1:])
        except NoReverseMatch:
            return reverse('plain_page', kwargs={'slug': split_link[0]})


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
        if not split_link:
            return ''
        try:
            return reverse(split_link[0], args=split_link[1:])
        except NoReverseMatch:
            return reverse('plain_page', kwargs={'slug': split_link[0]})


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
        processors=[SmartCrop(1200, 550)],  # wider crop with more height for faces
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
