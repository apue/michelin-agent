# Reuse and Cleanup Report

Status: accepted

## Reuse

- `profiling/vietnam_maps.py`: Unicode segmented matching, query cascade, per-item checkpoints, page recycling, and crash recovery.
- `profiling/optimized_batch.py`: distance calculation, Maps detail extraction, named-list selection, note commit verification, and full-list scrolling concept.
- `runner/io.py`: Michelin Algolia hit normalization concepts.

## Refactor

- Move proven logic into one installable `michelin_maps` package.
- Replace hard-coded country/date/list constants with CLI arguments and run manifests.
- Replace implicit status counts with an explicit coverage-versus-POI audit model.

## Delete

- Early `config`, `drivers`, `matcher`, and `runner` implementation: superseded contracts and wrong low-recall workflow.
- Entire `profiling` tree after extracting verified mechanisms: country-specific experiments and run output.
- `data`, `out`, `tmp`, `.pw-profile`, build metadata, and caches: private or generated state.
- `.automation` is operationally relevant signed-in state and remains local but is comprehensively ignored.

## Evidence

- `rg --files`, Python definition index, import scan, and targeted reads of both implementations.
- Vietnam E2E result: 190 source restaurants covered by 189 POIs, zero unresolved, and 189 notes verified.

## Risks

- Michelin public search configuration and Maps selectors may change; both are isolated behind small modules and contract tests.
