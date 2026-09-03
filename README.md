# Michelin Maps Agent

An agent-operated, end-to-end pipeline that fetches a complete Michelin Guide selection for a city, region, or country and saves it to a native Google Maps list. It uses Michelin's public search index and a signed-in Chrome session; it does not require Google Cloud billing or the Places API.

## What the agent owns

```text
scope -> fetch -> normalize -> save -> review misses -> apply reviews -> verify -> report
```

The review stage is performed by the agent with the browser. A user-facing unmatched list is produced only when the agent cannot confirm a POI after targeted name, address, coordinate, and public-web checks.

## Install

The repository uses `uv` and Python 3.11+:

```bash
uv sync
```

Start a dedicated signed-in Chrome profile with DevTools enabled. Keep the profile outside source control; `.automation/` is ignored for local use.

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9223 \
  --user-data-dir="$PWD/.automation/google-maps-chrome" \
  --no-first-run "https://www.google.com/maps"
```

Sign in interactively once. The automation never bypasses login, 2FA, CAPTCHAs, or account controls.

## End-to-end workflow

Choose a scope using `city:`, `region:`, or `country:`:

```bash
uv run michelin-maps fetch \
  --scope city:bangkok \
  --run-dir .runs/bangkok

uv run michelin-maps create-list \
  --list-name "Bangkok Michelin"

uv run michelin-maps run \
  --manifest .runs/bangkok/manifest.json \
  --run-dir .runs/bangkok \
  --list-name "Bangkok Michelin" \
  --list-url '<URL returned by create-list>'
```

The automatic pass writes `unmatched.csv`. The operating agent investigates those entries and writes `.runs/bangkok/review-overrides.json`; see [the review contract](skills/michelin-maps-e2e/references/review-overrides.md). Then:

```bash
uv run michelin-maps apply-reviews \
  --manifest .runs/bangkok/manifest.json \
  --run-dir .runs/bangkok \
  --reviews .runs/bangkok/review-overrides.json \
  --list-name "Bangkok Michelin" \
  --list-url '<LIST_URL>'

uv run michelin-maps verify \
  --manifest .runs/bangkok/manifest.json \
  --run-dir .runs/bangkok
```

Use `--retry-incomplete` on `run` after transient errors. Use `--discover-only` for a read-only matching pass. The default browser endpoint is `http://127.0.0.1:9223`.

## Artifacts and identity

Each run directory contains:

- `manifest.json`: normalized Michelin source records and completeness metadata.
- `audit.json`: queries, candidates, decisions, saves, and review evidence.
- `unmatched.csv`: only entries still requiring investigation.
- `review-overrides.json`: agent-authored reviewed mappings.
- `summary.md`: source coverage, unique POIs, shared mappings, and failures.

Michelin restaurant coverage and Google Maps POI count are deliberately separate. Multiple restaurants inside one venue can map to one POI with a combined note.

## Reliability model

- Atomic checkpoint after every restaurant.
- Resume skips completed source IDs.
- Maps pages are recycled every 25 items.
- A crashed page is recreated and retried once.
- Warm CDP profiles receive a 30-second connection budget.
- Notes are blurred, read back, and later verified across the full list.
- Verification scrolls lazy-loaded lists and compares all saved notes, not only the header count.

## Repository data policy

Restaurant datasets, run outputs, browser profiles, cookies, screenshots, credentials, caches, and build artifacts are ignored. Tests contain synthetic restaurant records only. Never force-add `.runs/`, `data/`, `.automation/`, `.pw-profile/`, or `.env`.

## Development

```bash
uv run python -m unittest discover -s tests -v
uv run michelin-maps --help
uv build
```

Architecture and acceptance decisions live in [`docs/harness`](docs/harness).
