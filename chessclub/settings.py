"""
Django settings for chessclub project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['CHESSCLUB_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
if 'DJANGO_DEBUG' in os.environ and os.environ['DJANGO_DEBUG'] == "1":
    DEBUG = True

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', '192.168.0.100', '192.168.1.120','192.168.1.107','192.168.1.123','wallaseychessclub.uk','www.wallaseychessclub.uk']


# Application definition

INSTALLED_APPS = [
	'league.apps.leagueConfig',
	'content.apps.ContentConfig',
    #'django.contrib.admin',
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_user_agents',
    'tinymce',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

ROOT_URLCONF = 'chessclub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'chessclub.context_processors.htmlobjects'
            ],
        },
    },
]

WSGI_APPLICATION = 'chessclub.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
# email details
EMAIL_HOST = 'mail.wallaseychessclub.uk'
EMAIL_PORT = 2525
EMAIL_USE_TLS = False    
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATIC_ROOT = os.path.join(os.environ["HOME"], "public_html/static/")
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.environ["HOME"], "public_html/media/")

if DEBUG:
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    #STATIC_ROOT = os.path.join(BASE_DIR, "static")


#only want this on server
if 'DJANGO_DEBUG' not in os.environ:
    SESSION_COOKIE_DOMAIN = 'wallaseychessclub.uk'
    SESSION_ENGINE='django.contrib.sessions.backends.db'

TINYMCE_SPELLCHECKER = True
TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'width': 800,
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'contextmenu': 'formats | link image',
    'menubar': True,
    'statusbar': True,
    'content_css' : '/static/styles/layout.css',
    'body_class' : 'tinymce',
    'body_id' : 'tinymce',
    'content_style' : "div {margin: 10px; border: 5px solid red; padding: 3px}",
    'style_formats': '{title: "test, selector: "div", classes: "review"}',
    'plugins' : "dvlist autolink lists link image charmap print preview anchor searchreplace visualblocks code "
    "fullscreen insertdatetime media table paste code help wordcount spellchecker",
    "toolbar": "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft "
    "aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor "
    "backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | "
    "fullscreen  preview save print | insertfile image media pageembed template link anchor codesample | "
    "a11ycheck ltr rtl | showcomments addcomment code wordcount spellchecker link,image",
    #'theme_advanced_buttons2': "spellchecker",
    'browser_spellcheck' : True,
    'gecko_spellcheck'   : True,
    }

APPEND_SLASH = True
