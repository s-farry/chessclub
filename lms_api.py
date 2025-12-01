import requests
from datetime import datetime

import django, os
os.environ["DJANGO_SETTINGS_MODULE"] = "chessclub.settings"
django.setup()

import argparse
import requests
import io
import dateutil.parser
import pytz


from league.models import LMSTeamFixture


server = "https://lms.englishchess.org.uk/lms/lmsrest/league"
date = datetime.now().strftime('%I:%M %A, %B %d, %Y')
print(f"Testing LMS Services {date} <br>")
print(f"Server: {server} <br>")

# URL for event results
url = f"{server}/club"

# Payload for POST request
data = {
    "org": 1353,
    'name' : "7WAL"
}

# Send POST request
response = requests.post(url, json=data)

lms_fixtures = []

lms_team_fixtures = LMSTeamFixture.objects.all()

# If we got JSON back, parse it
results = response.json()

for result in results:
    if "title" in result:
        # Print table data rows
        for row in result.get("data", []):
            lms_fixtures += [ row ]

matched_lms_fixtures = []

for l in lms_fixtures:
    home_team = l[0]
    away_team = l[2]
    home_score = float(l[1].replace(' ½', '0.5').replace('½','.5').replace(' - ',' ').split(' ')[0])
    away_score = float(l[1].replace(' ½', '0.5').replace('½','.5').replace(' - ',' ').split(' ')[1])
    date = l[3]
    time = l[4]
    dt = datetime.strptime(f'{date} {time}', '%a %d %b %y %H:%M')
    event = l[5]
    organisation=l[6]
    status=l[7]

    found_match = False

    for t in lms_team_fixtures:
        if home_team == t.home_team and away_team == t.away_team and dt == t.date and event == t.event and organisation == t.organisation:
            found_match = True
            print('updating ', t)
            if home_score != t.home_score or away_score != t.away_score:
                t.home_score= home_score
                t.away_score= away_score
                t = t.save()
            if status != t.status:
                t.status=status
                t = t.save()

            matched_lms_fixture_ids += [ t ]
    
    if not found_match:
        t = LMSTeamFixture(
            date = dt,
            organisation = organisation,
            event = event,
            home_team = home_team,
            away_team = away_team,
            home_score = home_score,
            away_score = away_score,
            status=status
        )

        t.save()
        print('creating ', t)
        matched_lms_fixtures += [ t ]

lms_team_fixtures = LMSTeamFixture.objects.all()


for t in lms_team_fixtures:
    # check if they are not in the latest lms response and if not delete
    if t not in matched_lms_fixtures:
        print('deleting ', t)
        t.delete()


date = datetime.now().strftime('%I:%M %A, %B %d, %Y')
print(f"Program Finished at {date}")