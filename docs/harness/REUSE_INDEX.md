# Reuse Index

Status: current

## Stable Extension Points

- New geographic scopes use `Scope`; do not add country-specific runners.
- Michelin response changes belong in `Restaurant.from_hit` or `MichelinClient`.
- Query improvements belong in `query_cascade` and must remain ordered and deduplicated.
- Maps UI changes belong in `MapsSession`; pipeline code must not contain selectors.
- New review evidence fields belong in the review schema and `apply_reviews` together.
- New run statuses must update `COMPLETE_STATUSES`, artifact counts, validation, and tests as one contract.

## Reusable Mechanisms

- `atomic_json`: per-item durable checkpoint writes.
- `query_cascade`: locale-tolerant retrieval sequence.
- `rank_candidate`/`acceptable`: deterministic hot-path matching.
- `MapsSession.new_page`: page recycling and crash recovery.
- `MapsSession.verify_list`: lazy-list load and note multiset verification.
- `apply_reviews`: one-to-one and shared-POI reviewed mappings.

## Avoid Parallel Implementations

Do not add separate scripts for Bangkok, Vietnam, Malaysia, or another destination. Add data/configuration or improve the generic contracts instead.
