
import datetime
from pytz import timezone

import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "chessclub.settings"
django.setup()

import argparse
import requests
import io
import dateutil.parser


from league.models import Team, TeamFixture
from content.models import event, album
from league.admin import standings_update, standings_save       

from league.utils import *

season = Season.objects.filter(name='2022/2023')[0]
teams = {t.name : t for t in Team.objects.filter(season=season)}


import xlrd

fixture_list = xlrd.open_workbook('table.xls', ignore_workbook_corruption=True)

sheet = fixture_list.sheets()[0]
nrows = sheet.nrows
ncols = sheet.ncols

fixtures  = []

for i in range(1, nrows):
    home = sheet.cell(i,0).value
    result = sheet.cell(i,1).value
    away = sheet.cell(i,2).value
    if home == '' or away == '': continue
    date = datetime.datetime.strptime((sheet.cell(i,3).value + ' ' + sheet.cell(i,4).value).replace('th','').replace('rd','').replace('st','').replace('nd',''), '%a %d %b %Y %H:%M')
    league = sheet.cell(i,5).value
    if 'wallasey' in home.lower():
        fixtures += [TeamFixture(team = teams[home], home = True, opponent = away, date = date)]
        print('%s v %s, %s, %s'%(home, away, league, date))
    if 'wallasey' in away.lower():
        fixtures += [TeamFixture(team = teams[away], home = False, opponent = home, date = date)]
        print('%s v %s, %s, %s'%(home, away, league, date))


for f in fixtures:
    f.save()
