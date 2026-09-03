---
name: michelin-maps-e2e
description: Fetch a complete Michelin Guide selection for a city, region, or country, save it to a native Google Maps list through a signed-in browser, review long-tail misses, and verify full coverage. Use for requests such as saving all Michelin restaurants in Bangkok or Malaysia. Do not use for ordinary restaurant recommendations or My Maps exports.
---

# Michelin Maps E2E

Operate the repository's `michelin-maps` CLI and the signed-in browser as one workflow. The desired result is verified source-restaurant coverage, not merely a script exit code.

## Authorization boundary

Fetching and `--discover-only` are read-only. Creating a list, saving POIs, editing notes, and applying reviews mutate the user's Google Maps account; perform them only when the current request authorizes that outcome. Never bypass login, 2FA, CAPTCHA, or Google access controls.

## Workflow

1. Inspect `README.md`, confirm `uv run michelin-maps --help`, and choose a gitignored `.runs/<scope>` directory.
2. Translate the requested extent into `city:<slug>`, `region:<slug>`, or `country:<slug>`. Run `fetch` and check that `metadata.expected_hits` equals the manifest restaurant count.
3. Connect to the dedicated signed-in Chrome CDP profile. Create a descriptive native list unless the user supplied one; retain its URL.
4. Run a small `--discover-only --limit 5` smoke test when the locale or Maps environment is new. Then run the full import. Let checkpoints handle interruption; use `--retry-incomplete` for transient misses or errors.
5. Treat unresolved entries as the agent's review queue. Read [review-overrides.md](references/review-overrides.md), inspect each restaurant with browser searches, and record evidence-backed mappings. Do not hand the first-pass misses directly to the user.
6. Apply the reviewed mappings. Shared Maps POIs may cover multiple Michelin source IDs and must use a combined note.
7. Run live `verify`. Require exact source coverage, the expected unique POI count, all notes loaded, no empty notes, and exact note-multiset equality.
8. Report the Maps URL, source coverage, unique POIs, automatically saved POIs, agent-reviewed POIs, shared mappings, errors, and only genuinely unresolved restaurants.

## Operational invariants

- Keep all source data and artifacts under `.runs/`; never stage them in Git.
- Optimize the automatic pass for recall, but do not knowingly save a wrong city, distant branch, hotel instead of restaurant, or unrelated business.
- Preserve per-query candidates and detail evidence in `audit.json`.
- Do not count a shared POI twice. Report both covered restaurants and unique POIs.
- Do not claim completion from the audit alone; live list verification is required after mutations.
- If Chrome or Playwright fails, read [browser-recovery.md](references/browser-recovery.md) before retrying.

## Stop conditions

Stop and ask the user only when authentication requires their interaction, the requested geographic scope is genuinely ambiguous, the target list choice is unknown and creating a new one would be inappropriate, or reviewed evidence cannot identify the remaining POIs. A Maps UI selector change is an engineering problem to diagnose, not an automatic user handoff.
