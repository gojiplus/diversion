# Changelog

## [Unreleased]

### Changed

- Adopt py-canon with uv, Ruff, Pyright, Sphinx, and shared CI workflows.
- Move application code into a typed `src/diversion` package; require Python 3.12+.
- Focus on tourist walks with editable starters for Paris, Hamburg, Frankfurt,
  and Seattle, plus key-free Google Maps previews.
- Route through selected stops; enforce walking-minute budgets for destination
  and circular walks, with separate visit allowances.
- Rank actual stop itineraries deterministically; make AI descriptions optional.
- Replace Folium with Google Maps using a separate, optional public browser key.

### Fixed

- Sample routes by geographic distance rather than vertex density.
- Preserve unrated sights and distinguish failed place searches from no matches.
- Bound API requests and detour candidates; retain required stop order.
- Remove unsupported walkability claims and AI-controlled scoring.
- Clear stale results, validate durations, and deduplicate route geometry.
- Add offline provider, planner, UI, map and installed-package checks.
