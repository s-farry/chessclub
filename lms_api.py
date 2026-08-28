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


from league.models import LMSTeamFixture, TEAM_SCORES

# Create a mapping from float score to integer key
SCORE_TO_KEY = {float(score.replace("½",".5")): key for key, score in TEAM_SCORES if key is not None and key >= 0}


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
    home_score_float = float(l[1].replace(' ½', '0.5').replace('½','.5').replace(' - ',' ').split(' ')[0])
    away_score_float = float(l[1].replace(' ½', '0.5').replace('½','.5').replace(' - ',' ').split(' ')[1])
    # Convert float scores to integer keys using TEAM_SCORES mapping
    home_score = SCORE_TO_KEY.get(home_score_float, 0)
    away_score = SCORE_TO_KEY.get(away_score_float, 0)
    date = l[3]
    time = l[4]
    dt = datetime.strptime(f'{date} {time}', '%a %d %b %y %H:%M')
    # Make timezone-aware to match Django database datetime
    dt = pytz.timezone('Europe/London').localize(dt)
    event = l[5]
    organisation=l[6]
    status=l[7]

    found_match = False

    if home_score == 0 and away_score == 0:
        home_score = None
        away_score = None

    for t in lms_team_fixtures:
        if home_team == t.home_team and away_team == t.away_team and dt == t.date and event == t.event and organisation == t.organisation:
            found_match = True
            updated = False

            if t.home_score != home_score or t.away_score != away_score:
                print(f'Score change for {t}: {t.home_score}-{t.away_score} -> {home_score}-{away_score}')
                t.home_score = home_score
                t.away_score = away_score
                t.save()
                updated = True
            if status != t.status:
                print(f'Status change for {t}: "{t.status}" -> "{status}"')
                t.status = status
                t.save()
                updated = True

            if not updated:
                print(f'No changes needed for {t}')

            matched_lms_fixtures += [ t ]
            break  # Found the match, stop searching
    
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

matched_ids = [f.id for f in matched_lms_fixtures]

for t in lms_team_fixtures:
    # check if they are not in the latest lms response and if not delete
    if t.id not in matched_ids:
        print('deleting ', t)
        t.delete()


date = datetime.now().strftime('%I:%M %A, %B %d, %Y')
print(f"Program Finished at {date}")