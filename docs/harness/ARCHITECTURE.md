# Architecture

Status: accepted

## System Shape

`michelin-maps` is a deterministic CLI operated by an agent. Code performs acquisition, normalization, browser actions, checkpointing, and verification. The agent uses the repository Skill to choose scope, create or identify the target list, inspect unresolved candidates in the signed-in browser, and write explicit review overrides.

## Modules

- `domain.py`: scope, restaurant, candidate, review, and audit contracts.
- `michelin.py`: Algolia query construction, pagination, and normalization.
- `queries.py`: Unicode normalization and country-independent query cascades.
- `matching.py`: segmented candidate scoring and acceptance guards.
- `maps.py`: CDP connection, Maps extraction, saving, notes, and list verification.
- `pipeline.py`: resumable automatic pass and reviewed override application.
- `artifacts.py`: atomic audit and human-readable output generation.
- `cli.py`: `fetch`, `run`, `apply-reviews`, and `verify` commands.
- `skills/michelin-maps-e2e`: agent operating instructions and review schema.

## Data Flow

```text
Scope -> Michelin Algolia -> normalized manifest -> Maps query cascade
      -> automatic saves -> unresolved audit -> agent browser review
      -> reviewed mappings -> saves/shared POIs -> full verifier -> summary
```

All mutable data lives under a caller-selected run directory, conventionally `.runs/<scope>/`, which is gitignored.

## Identity Model

Coverage is measured over Michelin restaurant IDs. Google Maps list size is measured over unique POIs. A reviewed mapping may cover multiple restaurant IDs with one POI and one combined note. Both numbers are reported.

## Reliability Boundaries

- Atomic checkpoint after each item.
- Completed statuses are idempotent on resume.
- New page after a configurable batch size.
- One page recreation on `Page crashed`.
- CDP connection timeout allows a warm profile to enumerate targets.
- Note values are blurred and read back before success is recorded.
- Live verification scrolls the entire list and compares the note multiset.

## Alternatives

- Google Places API: rejected because it requires billed Google Cloud access and still cannot bulk-save.
- My Maps: rejected because it does not provide the desired native iOS POI workflow.
- LLM matcher in the hot path: rejected as a default; deterministic recall plus agent review was faster and more auditable in the Vietnam run.
- Country-specific scripts: replaced by configuration and normalized contracts.
