# Specification

Status: accepted

## Goal

Given a Michelin geographic scope such as a city, region, or country, an agent can fetch the complete Michelin restaurant selection, save the restaurants into a native Google Maps list, review long-tail misses with the signed-in browser, and prove coverage with auditable artifacts.

## Requirements

- Accept `city`, `region`, or `country` scopes without country-specific code.
- Fetch and paginate Michelin's public Algolia search index; users need not prepare JSON.
- Preserve Michelin name, location, coordinates, award, cuisine, price, and URL.
- Generate a Unicode-aware query cascade and rank candidates by segmented name, city/address, and coordinate proximity.
- Optimize the automatic pass for recall while rejecting obvious wrong-city, non-restaurant, and distant candidates.
- Save to a named Google Maps list through an existing signed-in Chrome CDP session.
- Checkpoint every item, resume without repeating completed work, recycle pages, and recover from page crashes.
- Treat browser-assisted agent review as part of the normal workflow, not as user work.
- Model multiple Michelin restaurants sharing one Google Maps POI.
- Verify source coverage, unique POI count, list count, and every saved note.
- Emit `audit.json`, `review-overrides.json`, `unmatched.csv`, and `summary.md` under a gitignored run directory.
- Ship a Codex skill that tells a future agent how to operate the complete workflow.

## Non-goals

- Google Places API or a Google Cloud billing account.
- My Maps, KML, or custom placemarks.
- A zero-false-positive entity-resolution research system.
- Committing restaurant datasets, browser profiles, credentials, or run artifacts.
- Bypassing Google authentication, CAPTCHAs, or access controls.

## Constraints

- Google Maps has no supported free bulk-save API; browser selectors can drift.
- Michelin and Google Maps can represent restaurant identity differently.
- External writes occur only when the user authorizes a run and provides a target list.

## Acceptance Link

See [ACCEPTANCE.md](ACCEPTANCE.md).
