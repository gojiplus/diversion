# Diversion 🛤️

[![CI](https://github.com/gojiplus/diversion/actions/workflows/ci.yml/badge.svg)](https://github.com/gojiplus/diversion/actions/workflows/ci.yml)
[![Docs](https://github.com/gojiplus/diversion/actions/workflows/docs.yml/badge.svg)](https://github.com/gojiplus/diversion/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/gojiplus/diversion/blob/main/LICENSE)

Plan a city walk around sights, museums, gardens and food, with an explicit
walking budget. Diversion calculates routes through selected stops and separates
walking time from your visit allowance. Browse eight starter walks before
configuring an API key.

## City starters

| City | Walk | Stops and finish |
| --- | --- | --- |
| Paris | Marais: history and food | Place des Vosges → Carnavalet → Rue des Rosiers → Hôtel de Ville |
| Paris | Montmartre: squares and art | Abbesses → Place du Tertre → Musée de Montmartre → Sacré-Cœur |
| Hamburg | Speicherstadt to the Elbe | Wasserschloss → Maritime Museum → Elbphilharmonie |
| Hamburg | Alster arcades and gardens | Rathaus → Alsterarkaden → Jungfernstieg → Planten un Blomen |
| Frankfurt | Old town to the museum bank | Römerberg → Cathedral → Eiserner Steg → Städel |
| Frankfurt | Goethe and the market | Alte Oper → Goethe House → Kleinmarkthalle → Römerberg |
| Seattle | Market to Pioneer Square | Pike Place Market → Overlook Walk → Pier 62 → Pioneer Square |
| Seattle | Waterfront art and Seattle Center | Pier 62 → Olympic Sculpture Park → Space Needle |

These are editable editorial ideas, not verified itineraries with precomputed
times. The app links each idea to its official visitor guide and a Google Maps
preview. Routes, walking times and budgets are calculated when you plan. Check
opening hours, admission and access separately. Montmartre involves hills and
steps; the planner does not assess accessibility or terrain.

Sources: [Paris Je T’aime](https://parisjetaime.com/eng/article/village-paris-a922),
[Hamburg Tourism](https://www.hamburg-travel.com/discover-hamburg/areas/hafencity-speicherstadt/),
[Visit Frankfurt](https://www.visitfrankfurt.travel/en/experience/discover/highlights),
[Visit Seattle](https://visitseattle.org/things-to-do/sightseeing/on-the-waterfront/).

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use
Python 3.12 or newer:

```bash
uv sync --frozen
uv run streamlit run app.py
```

The city previews work immediately. For calculated options, enter a Google key
under **API configuration**, or copy `.env.example` to `.env` and set
`GOOGLE_MAPS_API_KEY`. Enable **Routes API** and **Places API (New)** with billing
in the Google Cloud project. Restrict this server key to those APIs and, where
possible, the server's IP addresses.

The embedded map is optional. Set `GOOGLE_MAPS_BROWSER_API_KEY` to a **separate**
key with Maps JavaScript API enabled and HTTP referrer restrictions for your app
(including localhost for local testing). This key is public in the browser;
the server key is never substituted for it. Without it, results still include
an itinerary and Google Maps directions link. Google route geometry is drawn
only on a Google map. Directions links preserve stop order and place IDs, but
Google recalculates the path when they open.

`OPENAI_API_KEY` is optional. Only clicking **Generate optional AI description**
sends the selected itinerary's stop names, types and walking time to OpenAI.
The existing `gpt-3.5-turbo` model supplies text; it never changes ranking.
Failure leaves the itinerary intact. Google receives endpoints, selected stop
queries and sampled coordinates during planning. Provider usage may incur charges.
Keys entered in the interface and calculated results stay in Streamlit session
state; the app does not persist or globally cache Google responses.

## Plan a walk

1. Customize a city starter or enter a start and finish, including the city.
2. Add up to two named stops, in visit order. Check the resolved names in results.
3. Set interests in landmarks, culture, parks, and food from zero to five.
4. Set extra walking minutes relative to the fastest direct option returned.
   For **Return to start**, set a total walking budget instead.
5. Set your allowance per intermediate stop, then select **Plan my walk**.

Every result includes all selected stops in their original order. The planner
also evaluates a few additional stops, inserting each where straight-line
travel is shortest while preserving your stop order, then checks the actual
walking route against the budget. No result silently drops a required stop.
If nothing fits, the app reports the shortest calculated over-budget duration.
Visit allowances are separate estimates; they exclude endpoints, queues and
opening-hour checks. A circular walk may retrace streets.

## How discovery and ranking work

Destination walks search a corridor along the fastest returned direct route,
using equal-distance samples about 500 meters apart and 300-meter search radii.
Sampling includes both endpoints and is capped at eight centers. Long walks
show a coverage warning. Circular walks search around the start, with a radius
of 40 meters per walking-budget minute, capped at 5 km. Nearby Search returns
up to 20 places per center, so suggestions are not exhaustive. Searches run with
at most four workers and explicit timeouts; partial failures are shown separately
from successful searches with no results. Unrated places remain eligible.

Candidate selection prefers interest match, with distance breaking ties. At most
three stop combinations are routed. Planning uses at most four Routes requests,
eight nearby searches, two named-stop searches and one loop-start search. A
selected stop outside the direct corridor is still routed, but its neighborhood
is not separately searched. Increasing the budget does not guarantee more options.

Ranking is deterministic and uses only stops included as routing waypoints.
Each stop takes its highest matching interest weight, divided by five. Ratings
make a modest adjustment shrunk toward zero with 50 prior reviews; missing
ratings are neutral. Stop values have diminishing returns (1, 1/2, 1/3), then
0.02 is subtracted per extra walking minute (per total minute for loops).
Scores are relative preference values, not ten-point quality ratings, and are
not displayed as such. The direct walk can rank first when detours offer little
value. Nearby places alone never improve a route's score.

This version does not measure scenic streets, noise, shade, sidewalk quality,
elevation, wheelchair access, opening hours or admission. Google walking-route
warnings and returned place-provider attributions are shown with the itinerary.

## Develop and test

The project follows [py-canon](https://github.com/gojiplus/py-canon): uv,
Ruff, Pyright, Google-style docstrings, pytest, and reusable GitHub workflows.

```bash
uv sync --frozen --all-groups
make ci
make ci-docker
make ci-docker PYTHON_IMAGE=python:3.14-slim
```

`make ci` checks formatting, lint, types, docstrings, tests with an 85% coverage
floor, Sphinx HTML and doctests, package metadata, and tests against an installed
wheel. `make conformance` runs preen and workflow security checks. The test suite
uses fake credentials and mocked API responses; it makes no paid API requests.
Docker CI uses a standard Python image and copies the project into the container,
excluding local credentials and environments.

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

The Streamlit entry point is `app.py`. Application code lives in
`src/diversion/`, tests in `tests/`, and Sphinx configuration in `docs/`.
Sphinx includes this README so setup instructions have one source.

## Deploy to Streamlit Community Cloud

Choose this repository, `main`, and `app.py`, and select Python 3.12 or newer.
Community Cloud [recognizes `uv.lock`](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
and installs the project and dependencies. The old `requirements.txt` is removed.
Users can supply keys through the sidebar; deployment does not require shared keys.
An existing deployment using Python 3.11 must change its Python version before
running this revision.

GitHub CI checks Python 3.12 and 3.14 and tests an installed wheel. The docs workflow
builds on pull requests and deploys on pushes to `main`; configure GitHub Pages
with **GitHub Actions** as its source to enable deployment.

PyPI publication is deferred because Diversion is deployed as an app. The manual
release workflow builds and validates artifacts through py-canon without
publishing them. Enable the standard trusted-publishing job if a PyPI release
is requested. See [the migration notes](https://github.com/gojiplus/diversion/blob/main/docs/migration.md)
for the adoption baseline and behavior changes.
