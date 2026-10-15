# Migration to py-canon

Diversion was adopted with `preen adopt` using the py-canon `v1.3.0` template.
`.copier-answers.yml` records the concrete baseline. Workflow callers track `v1`;
`uv.lock` records the exact py-canon commit used for Sphinx. Refresh the lock when
updating that shared dependency.

## Changes

- Python 3.12 is the minimum. Application code moved from `modules/` and `config/`
  into the installable `diversion` package; `app.py` remains the Streamlit entry point.
- `pyproject.toml` and `uv.lock` replace `requirements.txt`. Unused direct dependencies
  on googlemaps, pandas, and numpy were removed. Streamlit still uses pandas and
  numpy transitively.
- OpenAI descriptions use explicit session-specific clients, replacing process-wide
  key assignment. Ranking is now deterministic and does not require OpenAI.
- The app focuses on city walking. Percentage detour limits, driving, unsupported
  walkability controls and AI-generated route scores were removed.
- Actual place-ID waypoints, minute budgets, circular walks and editable starters
  for Paris, Hamburg, Frankfurt and Seattle replace proximity-only suggestions.
- Discovery samples distances rather than polyline vertices. Unrated places remain
  eligible; failed searches are distinguished from successful empty results.
- Folium and streamlit-folium were removed. An optional Google Maps JavaScript
  component displays Google geometry using a separate browser key. It is bundled
  in the Python wheel; no Node build is required to run the app.
- Requests have timeouts, check HTTP status, and clear stale results after failures.
  Duplicate geometry is filtered and fractional-second durations are accepted.

## Local verification

Run `make ci` for lint, types, docstrings, offline tests, coverage, documentation,
build metadata, and installed-wheel tests. Run `make conformance` for preen and
workflow security. `make ci-docker` repeats local CI in a standard Python image;
set `PYTHON_IMAGE=python:3.14-slim` for the upper CI version.

The tests exercise Streamlit through AppTest and mock external API responses.
They cannot establish whether particular Google or OpenAI credentials have access,
whether a route exists today, or whether an AI explanation is useful.

## Publishing exception

The standard's PyPI publishing job is deferred while this repository is deployed
only as a Streamlit application. The release workflow runs the shared build and
validation job on manual dispatch. It neither publishes to PyPI nor creates a
GitHub release. Remove this exception and add the standard trusted publisher when
a package release is requested. No PyPI version badge is shown before publication.

## Verification, 2026-10-14

The migration and city-walk redesign were tested as working-tree changes based
on Diversion commit `187650387e8e4a928ad4b71674638f44048100ab`. The resolved
py-canon documentation revision was `f13b560a7673cafb91a4b76070688ffcb50734f7`,
using the `v1.3.0` template baseline and preen `0.4.1`.

Local verification covers Ruff lint and formatting, Pyright, pydoclint, offline
pytest with branch coverage, Sphinx HTML and doctests, build metadata, and clean
wheel installations. The doctest builder currently finds no executable examples.
The Docker matrix uses standard Python 3.12 and 3.14 images. Preen's strict checks
skip its test check because pytest is run separately. Pre-commit includes new
untracked files; zizmor uses offline mode and py-canon's reusable-workflow policy.

A Chromium smoke test checks city tabs, preset selection, key-free previews,
mobile width, map geometry and markers with a mocked Google Maps runtime,
plain-text place labels, and map failure handling. No paid provider calls were
made. Hosted Actions, Pages deployment, live routing, browser-key authorization,
and PyPI publishing remain untested.
