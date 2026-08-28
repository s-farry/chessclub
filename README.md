# Wallasey Chess Club

A Django site for running a chess club: league and team fixture management, player
grades/ratings, news, events, photo galleries, and general club content. Live at
[wallaseychessclub.uk](https://www.wallaseychessclub.uk).

## Features

- **League management** (`league` app) — seasons, leagues, teams, fixtures, results,
  standings, committee members, and player records, including PGN storage for games.
- **Site content** (`content` app) — pages, news (with categories), events, image
  albums/galleries with smart cropping, puzzles, simuls, and downloadable documents.
- Rich text editing via `django-summernote`.
- Image handling/thumbnailing via `django-imagekit` and OpenCV-based face/smart crop.
- Integrations for pulling in Lichess data (`berserk`, `python-lichess`) and Google
  Drive/Sheets (`googledrive.py`, `credentials.json`/`token.json` — not committed).
- A handful of standalone scripts for one-off data tasks (grading imports, fixture
  imports, PGN extraction, etc.) in the project root.

## Requirements

- Python 3.12+
- Django 5.1 (see `requirements.txt` for the full dependency list)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the values (loaded automatically via
`python-dotenv`):

```
CHESSCLUB_SECRET_KEY=   # any long random string for local dev
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DJANGO_DEBUG=1
```

Then run migrations and start the dev server:

```bash
python manage.py migrate
python manage.py runserver
```

With `DJANGO_DEBUG=1` set, media is served from a local `media/` directory instead of
the production paths under `~/dev.wallaseychessclub.uk/`.

## Project layout

- `chessclub/` — project settings, root URLs, WSGI entry point.
- `league/` — league/fixture/player app.
- `content/` — pages, news, events, galleries app.
- `templates/`, `static/` — shared templates and static assets.

## Notes

`SECRET_KEY` and the email credentials are read from the environment
(`CHESSCLUB_SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`) rather than
hardcoded. **Any deployment (including the production server) needs a `.env` file
or equivalent environment variables set, or the app will fail to start.**

`credentials.json`, `token.json`, `media/`, and the `db.sqlite3*` files are excluded
via `.gitignore` and should never be committed.
